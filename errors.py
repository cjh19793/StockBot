"""분석 엔진 예외.

엔진(engine / montecarlo)은 실패를 예외로 던지고, 텔레그램 래퍼(analysis.analyze /
montecarlo.montecarlo)는 이를 잡아 기존과 동일하게 None 을 반환한다.
웹 API 는 이 예외를 HTTP 상태코드로 매핑한다.
"""


class AnalysisError(Exception):
    """분석 엔진 계열 예외의 베이스."""


class TickerNotFound(AnalysisError):
    """티커에 대한 가격 데이터를 찾지 못함 (또는 분석에 필요한 최소 데이터 부족)."""


class UpstreamDataError(AnalysisError):
    """외부 데이터 소스 오류로 분석을 완료할 수 없음."""
