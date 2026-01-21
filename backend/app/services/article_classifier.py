from typing import Dict, List, Tuple
import re
import logging

logger = logging.getLogger(__name__)

class ArticleClassifier:
    """하이브리드 방식의 의료 기사 분류기 (키워드 + 간단한 점수 시스템)"""

    def __init__(self, medical_keywords: List[str]):
        self.medical_keywords = medical_keywords

        # 카테고리별 키워드
        self.category_keywords = {
            '의정갈등': ['의정갈등', '의사파업', '의료파업', '전공의', '레지던트', '의대증원', '의료계', '의협', '대한의사협회', '집단휴진', '수련병원'],
            '병원': ['병원', '의원', '요양', '진료', '의사', '간호사', '응급실', '입원'],
            '제약': ['제약', '신약', '약', '의약품', '바이오', '임상', '임상시험'],
            '정책': ['보건복지부', '의료정책', '건강보험', '의료법', '의료개혁', '복지부'],
            '질병': ['질병', '암', '당뇨', '고혈압', '코로나', 'COVID', '감염', '바이러스', '독감'],
            '연구': ['연구', '논문', '학회', '의학', '의료기술', '진단', '치료법'],
            '기타': []
        }

    def classify_article(self, title: str, description: str = "") -> Tuple[bool, str, float, List[str]]:
        """
        기사를 분류하여 의료 관련 여부 판단

        Args:
            title: 기사 제목
            description: 기사 요약

        Returns:
            (is_medical, category, confidence_score, keywords)
            - is_medical: 의료 기사 여부
            - category: 의료 카테고리
            - confidence_score: 신뢰도 (0.0 ~ 1.0)
            - keywords: 추출된 키워드 리스트
        """
        text = f"{title} {description}".lower()
        found_keywords = []
        score = 0.0

        # 1단계: 키워드 매칭
        for keyword in self.medical_keywords:
            if keyword.lower() in text:
                found_keywords.append(keyword)
                # 제목에 있으면 가중치 2배
                if keyword.lower() in title.lower():
                    score += 2.0
                else:
                    score += 1.0

        # 2단계: 점수 정규화 (0.0 ~ 1.0)
        max_possible_score = len(self.medical_keywords) * 2.0
        confidence_score = min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

        # 신뢰도 보정: 키워드가 많을수록 신뢰도 증가 (필터링 전에 적용)
        if len(found_keywords) >= 1:
            confidence_score = max(confidence_score, min(0.5 + (len(found_keywords) * 0.1), 1.0))

        # 3단계: 의료 기사 판단 (신뢰도 0.04 이상)
        is_medical = confidence_score >= 0.04 and len(found_keywords) >= 1

        # 4단계: 카테고리 분류
        category = self._classify_category(text) if is_medical else None

        logger.debug(f"분류 결과 - 의료: {is_medical}, 카테고리: {category}, 신뢰도: {confidence_score:.2f}, 키워드: {found_keywords}")

        return is_medical, category, confidence_score, found_keywords

    def _classify_category(self, text: str) -> str:
        """텍스트를 기반으로 의료 카테고리 분류"""
        category_scores = {}

        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            category_scores[category] = score

        # 가장 높은 점수의 카테고리 반환
        max_category = max(category_scores.items(), key=lambda x: x[1])

        if max_category[1] > 0:
            return max_category[0]
        else:
            return '기타'

    def batch_classify(self, articles: List[Dict]) -> List[Dict]:
        """
        여러 기사를 일괄 분류

        Args:
            articles: 기사 딕셔너리 리스트

        Returns:
            분류 정보가 추가된 기사 리스트
        """
        classified_articles = []

        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')

            is_medical, category, confidence, keywords = self.classify_article(title, description)

            article['is_medical'] = is_medical
            article['category'] = category
            article['confidence_score'] = confidence
            article['keywords'] = keywords

            if is_medical:
                classified_articles.append(article)

        logger.info(f"분류 완료: 전체 {len(articles)}개 중 의료 기사 {len(classified_articles)}개")
        return classified_articles
