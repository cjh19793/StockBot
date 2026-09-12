"""텔레그램용 마크다운 포맷 (표현 전용).

기존 analysis._analyze 의 리포트 f-string 과 montecarlo.montecarlo 의 lines 조립을
그대로 옮겨온 것. 문구/서식 변경 없음. 웹 API 는 이 모듈을 사용하지 않는다.
"""
from models import AnalysisResult, MonteCarloResult


def format_analysis_report(r: AnalysisResult) -> str:
    price_label = f"*{r.price:.2f}* ({'실시간' if r.price_is_realtime else '전일 종가'})"

    buy_text = "\n".join(f"[매수] {s}" for s in r.buy_signals) or "없음"
    sell_text = "\n".join(f"[매도] {s}" for s in r.sell_signals) or "없음"

    if "Buy" in r.judgment:
        action = "*Buy Timing* - Consider split buying"
    elif "Sell" in r.judgment:
        action = "*Sell Timing* - Consider split selling"
    else:
        action = "*Watch* - Wait for signal confirmation"

    fg_text = (
        f"{r.fear_greed_score}점 - {r.fear_greed_label}"
        if r.fear_greed_score is not None
        else "가져오기 실패"
    )
    if r.news_sentiment:
        news_text = f"감성: {r.news_sentiment}\n" + "\n".join(
            f"  - {t}" for t in r.news_titles
        )
    else:
        news_text = "뉴스 없음"
    earnings_text = r.earnings or "정보 없음"

    return (
        f"*[{r.ticker}] {r.label} 분석 리포트*\n"
        f"기준: {r.now_str} | 조회: {r.asof_kst}\n"
        f"{r.market}\n"
        f"--------------------\n"
        f"현재가: {price_label}\n"
        f"목표가: {r.target_price:.2f} (+{r.target_pct * 100:.0f}%) | "
        f"손절가: {r.stop_loss:.2f} (-{r.stop_pct * 100:.0f}%)\n"
        f"거래량: {r.volume:,.0f}\n"
        f"RSI: {r.rsi:.1f} | MACD: {r.macd:.3f} | Stoch K: {r.stoch_k:.1f}\n"
        f"MA5: {r.ma5:.2f} | MA20: {r.ma20:.2f}\n"
        f"BB상단: {r.bb_upper:.2f} | BB하단: {r.bb_lower:.2f}\n\n"
        f"--------------------\n"
        f"*시장 심리*\n"
        f"공포탐욕지수: {fg_text}\n"
        f"실적 발표: {earnings_text}\n\n"
        f"*뉴스 감성*\n"
        f"{news_text}\n\n"
        f"--------------------\n"
        f"*매수 신호 ({r.buy_score}점)*\n{buy_text}\n\n"
        f"*매도 신호 ({r.sell_score}점)*\n{sell_text}\n\n"
        f"--------------------\n"
        f"최종 판정: *{r.judgment}*\n{action}"
    )


def format_montecarlo(r: MonteCarloResult) -> str:
    lines = [
        f"*[{r.ticker}] Monte Carlo - {r.label}*",
        f"Simulations: {r.simulations} | Data: {r.period}\n",
    ]
    for h in r.holds:
        lines.append(
            f"--- Hold {h.hold_days} days ---\n"
            f"Win Rate: {h.win_rate:.1f}% | Grade: {h.grade}\n"
            f"Avg Return: {h.avg_return:+.1f}%\n"
            f"Max Profit: {h.max_profit:+.1f}% | Max Loss: {h.max_loss:+.1f}%"
        )
    lines.append(
        f"\nBest Period: {r.best_hold_days} days (Win Rate: {r.best_win_rate:.1f}%)"
    )
    lines.append("\n*Caution: Based on past data.\nDoes not guarantee future returns.*")
    return "\n".join(lines)
