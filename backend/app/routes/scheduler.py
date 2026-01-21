from flask import Blueprint, jsonify, current_app
from app.services.news_collector import NewsCollector
from app.services.article_classifier import ArticleClassifier
from app.models.article import Article
from app import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')

@bp.route('/collect', methods=['POST'])
def collect_articles():
    """기사 수집 수동 실행"""
    try:
        # 설정 가져오기
        client_id = current_app.config.get('NAVER_CLIENT_ID')
        client_secret = current_app.config.get('NAVER_CLIENT_SECRET')
        medical_keywords = current_app.config.get('MEDICAL_KEYWORDS')
        max_articles = current_app.config.get('MAX_ARTICLES_PER_DAY')

        if not client_id or not client_secret:
            return jsonify({
                'error': 'Naver API 키가 설정되지 않았습니다',
                'message': 'backend/.env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요. 또는 샘플 데이터를 사용하세요.',
                'docs': 'https://developers.naver.com에서 API 키를 발급받을 수 있습니다.'
            }), 400

        # 1단계: 기사 수집
        collector = NewsCollector(client_id, client_secret)
        articles = collector.collect_medical_articles(max_articles=max_articles)

        logger.info(f"수집된 기사: {len(articles)}개")

        # 2단계: 의료 기사 분류
        classifier = ArticleClassifier(medical_keywords)
        medical_articles = classifier.batch_classify(articles)

        logger.info(f"의료 기사: {len(medical_articles)}개")

        # 3단계: 데이터베이스 저장
        saved_count = 0
        skipped_count = 0

        for article_data in medical_articles:
            # URL 중복 체크
            existing = Article.query.filter_by(url=article_data['url']).first()
            if existing:
                skipped_count += 1
                continue

            article = Article(
                title=article_data['title'],
                description=article_data['description'],
                url=article_data['url'],
                source=article_data['source'],
                published_date=article_data['published_date'],
                is_medical=article_data['is_medical'],
                category=article_data['category'],
                keywords=article_data['keywords'],
                confidence_score=article_data['confidence_score']
            )

            db.session.add(article)
            saved_count += 1

        db.session.commit()

        logger.info(f"저장: {saved_count}개, 중복 스킵: {skipped_count}개")

        return jsonify({
            'success': True,
            'collected': len(articles),
            'medical': len(medical_articles),
            'saved': saved_count,
            'skipped': skipped_count
        })

    except Exception as e:
        logger.error(f"기사 수집 중 오류: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/status', methods=['GET'])
def get_status():
    """스케줄러 상태 조회"""
    return jsonify({
        'status': 'running',
        'collection_time': current_app.config.get('ARTICLE_COLLECTION_TIME'),
        'max_articles_per_day': current_app.config.get('MAX_ARTICLES_PER_DAY')
    })

@bp.route('/collect-historical', methods=['POST'])
def collect_historical_articles():
    """
    과거 7일치 기사 일괄 수집 (일회성 작업)

    주의: 이 엔드포인트는 대량의 데이터를 수집하므로 실행 시간이 오래 걸릴 수 있습니다.
    """
    try:
        # 설정 가져오기
        client_id = current_app.config.get('NAVER_CLIENT_ID')
        client_secret = current_app.config.get('NAVER_CLIENT_SECRET')
        medical_keywords = current_app.config.get('MEDICAL_KEYWORDS')

        if not client_id or not client_secret:
            return jsonify({
                'error': 'Naver API 키가 설정되지 않았습니다'
            }), 400

        # 서비스 초기화
        collector = NewsCollector(client_id, client_secret)
        classifier = ArticleClassifier(medical_keywords)

        # 날짜 범위 계산 (지난 7일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        logger.info(f"과거 데이터 수집 시작: {start_date.date()} ~ {end_date.date()}")

        # 의료 키워드 목록
        medical_queries = ['의료', '병원', '건강', '질병', '치료', '신약']

        total_collected = 0
        total_saved = 0
        total_skipped = 0

        # 각 키워드별로 수집
        for query in medical_queries:
            logger.info(f"키워드 '{query}' 수집 중...")

            # 페이지네이션으로 여러 페이지 수집 (최대 10페이지)
            for start in range(1, 1000, 100):
                articles = collector.collect_articles(
                    query=query,
                    display=100,
                    start=start
                )

                if not articles:
                    break

                # 날짜 필터링
                filtered_articles = []
                should_stop = False

                for article in articles:
                    pub_date = article.get('published_date')

                    if pub_date < start_date:
                        # 7일보다 오래된 기사가 나오면 수집 중단
                        should_stop = True
                        break

                    if start_date <= pub_date <= end_date:
                        filtered_articles.append(article)

                total_collected += len(filtered_articles)

                if filtered_articles:
                    # 의료 기사 분류
                    classified = classifier.batch_classify(filtered_articles)

                    # 데이터베이스에 저장
                    for article_data in classified:
                        # 중복 체크 (URL 기준)
                        existing = Article.query.filter_by(url=article_data['url']).first()
                        if existing:
                            total_skipped += 1
                            continue

                        # 새 기사 저장
                        article = Article(
                            title=article_data['title'],
                            description=article_data['description'],
                            url=article_data['url'],
                            source=article_data['source'],
                            published_date=article_data['published_date'],
                            is_medical=article_data['is_medical'],
                            category=article_data['category'],
                            keywords=article_data['keywords'],
                            confidence_score=article_data['confidence_score']
                        )
                        db.session.add(article)
                        total_saved += 1

                    db.session.commit()

                if should_stop:
                    break

            logger.info(f"키워드 '{query}' 완료")

        logger.info(f"과거 데이터 수집 완료 - 수집: {total_collected}개, 저장: {total_saved}개, 중복: {total_skipped}개")

        return jsonify({
            'success': True,
            'period': f"{start_date.date()} ~ {end_date.date()}",
            'collected': total_collected,
            'saved': total_saved,
            'skipped': total_skipped
        })

    except Exception as e:
        logger.error(f"과거 데이터 수집 중 오류: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
