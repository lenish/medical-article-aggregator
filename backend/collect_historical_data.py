#!/usr/bin/env python
"""
지난 7일치 의료 기사 수집 스크립트
"""
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Article
from app.services.news_collector import NewsCollector
from app.services.article_classifier import ArticleClassifier
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def collect_historical_data(days: int = 7):
    """
    지난 N일간의 의료 기사 수집

    Args:
        days: 수집할 과거 일수 (기본값: 7일)
    """
    app = create_app()

    with app.app_context():
        # 서비스 초기화
        collector = NewsCollector(
            client_id=Config.NAVER_CLIENT_ID,
            client_secret=Config.NAVER_CLIENT_SECRET
        )
        classifier = ArticleClassifier(medical_keywords=Config.MEDICAL_KEYWORDS)

        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        logger.info(f"수집 기간: {start_date.date()} ~ {end_date.date()}")

        # 의료 키워드 목록
        medical_queries = ['의료', '병원', '건강', '질병', '치료', '신약']

        total_collected = 0
        total_saved = 0
        total_skipped = 0

        # 각 키워드별로 수집
        for query in medical_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"키워드: '{query}' 수집 시작")
            logger.info(f"{'='*60}")

            query_collected = 0
            query_saved = 0

            # 페이지네이션으로 여러 페이지 수집
            # Naver API: start는 1부터 시작, 최대 1000까지
            for start in range(1, 1000, 100):
                logger.info(f"  페이지 {start//100 + 1} 수집 중... (start={start})")

                articles = collector.collect_articles(
                    query=query,
                    display=100,
                    start=start
                )

                if not articles:
                    logger.info(f"  더 이상 기사가 없습니다.")
                    break

                # 날짜 필터링
                filtered_articles = []
                should_stop = False

                for article in articles:
                    pub_date = article.get('published_date')

                    if pub_date < start_date:
                        # 7일보다 오래된 기사가 나오면 수집 중단
                        logger.info(f"  7일 이전 기사 발견 ({pub_date.date()}), 수집 중단")
                        should_stop = True
                        break

                    if start_date <= pub_date <= end_date:
                        filtered_articles.append(article)

                query_collected += len(filtered_articles)
                logger.info(f"  날짜 필터링 결과: {len(filtered_articles)}개 (원본: {len(articles)}개)")

                if filtered_articles:
                    # 의료 기사 분류
                    classified = classifier.batch_classify(filtered_articles)
                    logger.info(f"  의료 기사 분류 결과: {len(classified)}개")

                    # 데이터베이스에 저장
                    saved_count = 0
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
                            category=article_data.get('category'),
                            confidence_score=article_data.get('confidence_score', 0.0),
                            keywords=','.join(article_data.get('keywords', []))
                        )
                        db.session.add(article)
                        saved_count += 1

                    db.session.commit()
                    query_saved += saved_count
                    logger.info(f"  데이터베이스 저장: {saved_count}개")

                if should_stop:
                    break

            total_collected += query_collected
            total_saved += query_saved
            logger.info(f"키워드 '{query}' 완료 - 수집: {query_collected}개, 저장: {query_saved}개")

        # 최종 결과
        logger.info(f"\n{'='*60}")
        logger.info(f"수집 완료!")
        logger.info(f"{'='*60}")
        logger.info(f"총 수집된 기사: {total_collected}개")
        logger.info(f"총 저장된 기사: {total_saved}개")
        logger.info(f"중복으로 건너뛴 기사: {total_skipped}개")
        logger.info(f"저장 성공률: {(total_saved/(total_collected or 1))*100:.1f}%")

        return {
            'collected': total_collected,
            'saved': total_saved,
            'skipped': total_skipped
        }

if __name__ == '__main__':
    # 기본값: 지난 7일
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    logger.info(f"지난 {days}일치 의료 기사 수집 시작...\n")

    result = collect_historical_data(days=days)

    logger.info(f"\n✅ 과거 데이터 수집 완료!")
    logger.info(f"   수집: {result['collected']}개")
    logger.info(f"   저장: {result['saved']}개")
    logger.info(f"   중복 제외: {result['skipped']}개")
