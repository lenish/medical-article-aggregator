import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """기본 설정"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///medical_articles.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Naver News API 설정
    NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
    NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

    # 스케줄러 설정
    SCHEDULER_API_ENABLED = True

    # 의료 관련 키워드
    MEDICAL_KEYWORDS = [
        '의료', '병원', '의사', '간호사', '환자', '질병', '치료',
        '약', '수술', '건강', '보건', '코로나', 'COVID', '백신',
        '진료', '암', '당뇨', '고혈압', '의학', '한의학', '약국',
        '제약', '신약', '임상', '진단', '검사', '의료기기'
    ]

    # 기사 수집 설정
    MAX_ARTICLES_PER_DAY = 100
    ARTICLE_COLLECTION_TIME = "09:00"  # 매일 수집 시간

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
