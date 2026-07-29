"""
영문 제목을 한글로 번역하는 공용 유틸.
GNews, WHO, CDC 스크립트가 공통으로 사용한다.

deep-translator(구글 번역 무료 웹 엔드포인트, API 키 불필요)를 쓰기 때문에
비공식 방식이라 가끔 실패할 수 있다. 실패해도 예외를 던지지 않고
조용히 원문을 그대로 반환한다 (번역 실패가 데이터 수집 자체를 막으면 안 되므로).
"""

try:
    from deep_translator import GoogleTranslator
    _TRANSLATOR_AVAILABLE = True
except ImportError:
    _TRANSLATOR_AVAILABLE = False


def translate_to_korean(text):
    """영문 텍스트를 한글로 번역. 번역이 안 되면(패키지 없음/네트워크 오류/
    비공식 구글 번역 엔드포인트 장애 등) 조용히 원문을 그대로 반환한다."""

    if not text or not _TRANSLATOR_AVAILABLE:
        return text

    try:
        translated = GoogleTranslator(source="en", target="ko").translate(text)
        return translated or text
    except Exception as e:
        print("번역 실패, 원문 사용:", e)
        return text
