"""공통 유틸리티: yfinance 컬럼 평탄화, TTL 캐시."""
import functools
import threading
import time

import pandas as pd


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """단일 티커 다운로드 시 생기는 MultiIndex 컬럼을 단순 컬럼으로 변환."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def ttl_cache(seconds: float, cache_none: bool = False):
    """인자 기준 TTL 캐시 (스레드 안전).

    cache_none=False 이면 None 결과는 캐시하지 않아 일시적 실패가 오래 남지 않는다.
    """
    def decorator(func):
        store: dict = {}
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            with lock:
                hit = store.get(key)
                if hit is not None and now - hit[1] < seconds:
                    return hit[0]
            result = func(*args, **kwargs)
            if result is not None or cache_none:
                with lock:
                    store[key] = (result, now)
            return result

        wrapper.cache_clear = store.clear  # 테스트용
        return wrapper

    return decorator
