"""기술적 지표 계산."""
import numpy as np
import pandas as pd


def get_value(series) -> float:
    """시리즈/배열의 마지막 스칼라 값."""
    return float(np.asarray(series).flatten()[-1])


def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """이동평균 · 볼린저 · RSI · MACD · 스토캐스틱을 추가한 새 데이터프레임 반환.

    입력 df 는 변경하지 않는다(캐시된 원본 공유 시 경합 방지).
    """
    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()

    stddev = df["Close"].rolling(20).std()
    df["stddev"] = stddev
    df["Upper"] = df["MA20"] + stddev * 2
    df["Lower"] = df["MA20"] - stddev * 2

    # RSI (Wilder 14) — loss 가 0 이어도 0 나눗셈이 나지 않도록 처리
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    df["RSI"] = rsi.mask((loss == 0) & (gain > 0), 100.0)

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    low14 = df["Low"].rolling(14).min()
    high14 = df["High"].rolling(14).max()
    rng = (high14 - low14).replace(0, np.nan)
    df["Stoch_K"] = 100 * (df["Close"] - low14) / rng
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean()

    # ATR(14) — True Range 는 갭까지 포함한 실질 변동폭. RSI 와 동일한 14봉 창 사용.
    # 첫 행은 전일 종가가 없어 TR 자체가 NaN이며, 이후 컬럼들과 동일하게
    # rolling(14) 결과도 초반 구간은 자연스럽게 NaN으로 남긴다 (별도 보정 없음).
    prev_close = df["Close"].shift(1)
    true_range = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    df["ATR"] = true_range.rolling(14).mean()
    df["ATR_Pct"] = df["ATR"] / df["Close"]

    # 지지/저항 — 최근 20봉 실제 저가/고가 (볼린저와 달리 통계 밴드가 아닌 가격구조 기준)
    df["Support"] = df["Low"].rolling(20).min()
    df["Resistance"] = df["High"].rolling(20).max()

    return df
