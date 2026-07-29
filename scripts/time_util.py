"""
모든 스크립트가 "마지막 업데이트/갱신" 시각을 한국시간(KST) 기준으로
일관되게 남기도록 만든 공용 유틸.

GitHub Actions 실행 서버는 기본 시간대가 UTC라서, datetime.now()를 그냥 쓰면
한국시간보다 9시간 느리게 찍힌다. 이 모듈의 kst_now_str()을 대신 쓴다.
"""

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def kst_now():
    """현재 시각을 KST 기준 datetime으로 반환"""
    return datetime.now(KST)


def kst_now_str(fmt="%Y-%m-%d %H:%M"):
    """현재 시각을 KST 기준 문자열로 반환 (기본: 'YYYY-MM-DD HH:MM')"""
    return kst_now().strftime(fmt)
