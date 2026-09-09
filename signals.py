"""매수/매도 신호 스코어링."""
from indicators import get_value


def detect_signal(df):
    buy_signals, sell_signals = [], []
    buy_score, sell_score = 0, 0

    curr_close = get_value(df["Close"])
    curr_rsi = get_value(df["RSI"])
    curr_upper = get_value(df["Upper"])
    curr_lower = get_value(df["Lower"])
    curr_ma20 = get_value(df["MA20"])
    curr_ma5 = get_value(df["MA5"])
    curr_volume = get_value(df["Volume"])
    avg_volume = get_value(df["Volume"].rolling(20).mean().dropna())

    macd = get_value(df["MACD"])
    macd_signal = get_value(df["MACD_signal"])
    prev_macd = get_value(df["MACD"].iloc[:-1])
    prev_macd_signal = get_value(df["MACD_signal"].iloc[:-1])

    stoch_k = get_value(df["Stoch_K"])
    stoch_d = get_value(df["Stoch_D"])
    prev_stoch_k = get_value(df["Stoch_K"].iloc[:-1])
    prev_stoch_d = get_value(df["Stoch_D"].iloc[:-1])
    prev_ma5 = get_value(df["MA5"].iloc[:-1])
    prev_ma20 = get_value(df["MA20"].iloc[:-1])

    # 매수 조건
    if curr_rsi <= 30:
        buy_signals.append(f"RSI 과매도 ({curr_rsi:.1f}) - 반등 가능성 높음")
        buy_score += 1
    elif curr_rsi <= 40:
        buy_signals.append(f"RSI 저점 근접 ({curr_rsi:.1f}) - 약한 매수 구간")
        buy_score += 1

    if curr_close <= curr_lower:
        buy_signals.append(f"볼린저 하단 이탈 ({curr_lower:.2f}) - 단기 반등 기대")
        buy_score += 1
    elif curr_close <= curr_lower * 1.02:
        buy_signals.append(f"볼린저 하단 근접 ({curr_lower:.2f}) - 지지선 테스트")
        buy_score += 1

    if prev_macd < prev_macd_signal and macd > macd_signal:
        buy_signals.append("MACD 골든크로스 - 상승 전환 신호")
        buy_score += 2

    if prev_stoch_k < prev_stoch_d and stoch_k > stoch_d and stoch_k < 20:
        buy_signals.append(f"스토캐스틱 골든크로스 ({stoch_k:.1f}) - 과매도 반등")
        buy_score += 1

    if avg_volume > 0 and curr_volume >= avg_volume * 2.0:
        buy_signals.append(f"거래량 폭증 ({curr_volume / avg_volume:.1f}배) - 강한 매수세")
        buy_score += 2
    elif avg_volume > 0 and curr_volume >= avg_volume * 1.5:
        buy_signals.append(f"거래량 급증 ({curr_volume / avg_volume:.1f}배) - 매수세 증가")
        buy_score += 1

    if prev_ma5 < prev_ma20 and curr_ma5 > curr_ma20:
        buy_signals.append("MA 골든크로스 - 중기 상승 전환")
        buy_score += 2

    if curr_close > curr_ma20 and curr_close > curr_ma5:
        buy_signals.append("이동평균선 위 안착 - 상승 추세")
        buy_score += 1

    # 매도 조건
    if curr_rsi >= 70:
        sell_signals.append(f"RSI 과매수 ({curr_rsi:.1f}) - 조정 가능성")
        sell_score += 1
    elif curr_rsi >= 60:
        sell_signals.append(f"RSI 고점 근접 ({curr_rsi:.1f}) - 약한 매도 구간")
        sell_score += 1

    if curr_close >= curr_upper:
        sell_signals.append(f"볼린저 상단 이탈 ({curr_upper:.2f}) - 단기 조정 가능")
        sell_score += 1
    elif curr_close >= curr_upper * 0.98:
        sell_signals.append(f"볼린저 상단 근접 ({curr_upper:.2f}) - 저항선 테스트")
        sell_score += 1

    if prev_macd > prev_macd_signal and macd < macd_signal:
        sell_signals.append("MACD 데드크로스 - 하락 전환 신호")
        sell_score += 2

    if prev_stoch_k > prev_stoch_d and stoch_k < stoch_d and stoch_k > 80:
        sell_signals.append(f"스토캐스틱 데드크로스 ({stoch_k:.1f}) - 과매수 하락")
        sell_score += 1

    if avg_volume > 0 and curr_volume < avg_volume * 0.5:
        sell_signals.append(f"거래량 급감 ({curr_volume / avg_volume:.1f}배) - 매수세 소멸")
        sell_score += 1

    if prev_ma5 > prev_ma20 and curr_ma5 < curr_ma20:
        sell_signals.append("MA 데드크로스 - 중기 하락 전환")
        sell_score += 2

    if curr_close < curr_ma20 and curr_close < curr_ma5:
        sell_signals.append("이동평균선 아래 위치 - 하락 추세")
        sell_score += 1

    return buy_score, buy_signals, sell_score, sell_signals


def final_judgment(buy_score, sell_score):
    if buy_score == 0 and sell_score == 0:
        return "[Neutral] Watch", "gray", "Neutral"
    if buy_score > sell_score:
        if buy_score >= 6:
            label = "Strong Buy"
        elif buy_score >= 4:
            label = "Buy"
        elif buy_score >= 2:
            label = "Weak Buy"
        else:
            label = "Slight Buy"
        return f"[Buy] {label}", "blue", f"[Buy] {label}"
    if sell_score > buy_score:
        if sell_score >= 6:
            label = "Strong Sell"
        elif sell_score >= 4:
            label = "Sell"
        elif sell_score >= 2:
            label = "Weak Sell"
        else:
            label = "Slight Sell"
        return f"[Sell] {label}", "red", f"[Sell] {label}"
    return "[Neutral] Balance", "gray", "Balance"
