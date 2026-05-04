import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import os
import datetime
import pytz
import asyncio
import random

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 설정
# ==========================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID        = os.environ.get('CHAT_ID')

MODE_CONFIG = {
    '단타': {'interval': '5m',  'period': '5d',  'label': '5분봉 (단타)',   'bar_width': 0.003},
    '스윙': {'interval': '1h',  'period': '60d', 'label': '1시간봉 (스윙)', 'bar_width': 0.03},
    '기본': {'interval': '1d',  'period': '6mo', 'label': '일봉 (기본)',    'bar_width': 0.6},
}

# ==========================================
# 2. 데이터 가져오기
# ==========================================
def get_df(ticker, mode='기본'):
    try:
        cfg = MODE_CONFIG[mode]
        df  = yf.download(ticker, period=cfg['period'], interval=cfg['interval'], progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        if df.empty:
            return None
        if mode == '기본':
            df.index = pd.to_datetime(df.index).normalize()
        return df
    except Exception as e:
        print(f"yfinance 오류: {e}")
        return None

# ==========================================
# 3. 지표 계산
# ==========================================
def get_value(series):
    return float(np.array(series).flatten()[-1])

def calc_indicators(df):
    df['MA20']   = df['Close'].rolling(20).mean()
    df['stddev'] = df['Close'].rolling(20).std()
    df['Upper']  = df['MA20'] + df['stddev'] * 2
    df['Lower']  = df['MA20'] - df['stddev'] * 2

    delta        = df['Close'].diff()
    gain         = delta.where(delta > 0, 0).rolling(14).mean()
    loss         = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI']    = 100 - (100 / (1 + gain / loss))

    ema12             = df['Close'].ewm(span=12, adjust=False).mean()
    ema26             = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD']        = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist']   = df['MACD'] - df['MACD_signal']

    low14         = df['Low'].rolling(14).min()
    high14        = df['High'].rolling(14).max()
    df['Stoch_K'] = 100 * (df['Close'] - low14) / (high14 - low14)
    df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
    df['MA5']     = df['Close'].rolling(5).mean()
    df['MA60']    = df['Close'].rolling(60).mean()

    return df

# ==========================================
# 4. 매수/매도 신호
# ==========================================
def detect_signal(df):
    buy_signals, sell_signals = [], []
    buy_score, sell_score = 0, 0

    curr_close  = get_value(df['Close'])
    curr_rsi    = get_value(df['RSI'])
    curr_upper  = get_value(df['Upper'])
    curr_lower  = get_value(df['Lower'])
    curr_ma20   = get_value(df['MA20'])
    curr_ma5    = get_value(df['MA5'])
    curr_volume = get_value(df['Volume'])
    avg_volume  = get_value(df['Volume'].rolling(20).mean().dropna())

    macd             = get_value(df['MACD'])
    macd_signal      = get_value(df['MACD_signal'])
    prev_macd        = get_value(df['MACD'].iloc[:-1])
    prev_macd_signal = get_value(df['MACD_signal'].iloc[:-1])

    stoch_k      = get_value(df['Stoch_K'])
    stoch_d      = get_value(df['Stoch_D'])
    prev_stoch_k = get_value(df['Stoch_K'].iloc[:-1])
    prev_stoch_d = get_value(df['Stoch_D'].iloc[:-1])
    prev_ma5     = get_value(df['MA5'].iloc[:-1])
    prev_ma20    = get_value(df['MA20'].iloc[:-1])

    # 매수 조건
    if curr_rsi <= 30:
        buy_signals.append(f"RSI 과매도 ({curr_rsi:.1f}) - 반등 가능성 높음"); buy_score += 1
    elif curr_rsi <= 40:
        buy_signals.append(f"RSI 저점 근접 ({curr_rsi:.1f}) - 약한 매수 구간"); buy_score += 1

    if curr_close <= curr_lower:
        buy_signals.append(f"볼린저 하단 이탈 ({curr_lower:.2f}) - 단기 반등 기대"); buy_score += 1
    elif curr_close <= curr_lower * 1.02:
        buy_signals.append(f"볼린저 하단 근접 ({curr_lower:.2f}) - 지지선 테스트"); buy_score += 1

    if prev_macd < prev_macd_signal and macd > macd_signal:
        buy_signals.append("MACD 골든크로스 - 상승 전환 신호"); buy_score += 2

    if prev_stoch_k < prev_stoch_d and stoch_k > stoch_d and stoch_k < 20:
        buy_signals.append(f"스토캐스틱 골든크로스 ({stoch_k:.1f}) - 과매도 반등"); buy_score += 1

    if avg_volume > 0 and curr_volume >= avg_volume * 2.0:
        buy_signals.append(f"거래량 폭증 ({curr_volume/avg_volume:.1f}배) - 강한 매수세"); buy_score += 2
    elif avg_volume > 0 and curr_volume >= avg_volume * 1.5:
        buy_signals.append(f"거래량 급증 ({curr_volume/avg_volume:.1f}배) - 매수세 증가"); buy_score += 1

    if prev_ma5 < prev_ma20 and curr_ma5 > curr_ma20:
        buy_signals.append("MA 골든크로스 - 중기 상승 전환"); buy_score += 2

    if curr_close > curr_ma20 and curr_close > curr_ma5:
        buy_signals.append("이동평균선 위 안착 - 상승 추세"); buy_score += 1

    # 매도 조건
    if curr_rsi >= 70:
        sell_signals.append(f"RSI 과매수 ({curr_rsi:.1f}) - 조정 가능성"); sell_score += 1
    elif curr_rsi >= 60:
        sell_signals.append(f"RSI 고점 근접 ({curr_rsi:.1f}) - 약한 매도 구간"); sell_score += 1

    if curr_close >= curr_upper:
        sell_signals.append(f"볼린저 상단 이탈 ({curr_upper:.2f}) - 단기 조정 가능"); sell_score += 1
    elif curr_close >= curr_upper * 0.98:
        sell_signals.append(f"볼린저 상단 근접 ({curr_upper:.2f}) - 저항선 테스트"); sell_score += 1

    if prev_macd > prev_macd_signal and macd < macd_signal:
        sell_signals.append("MACD 데드크로스 - 하락 전환 신호"); sell_score += 2

    if prev_stoch_k > prev_stoch_d and stoch_k < stoch_d and stoch_k > 80:
        sell_signals.append(f"스토캐스틱 데드크로스 ({stoch_k:.1f}) - 과매수 하락"); sell_score += 1

    if avg_volume > 0 and curr_volume < avg_volume * 0.5:
        sell_signals.append(f"거래량 급감 ({curr_volume/avg_volume:.1f}배) - 매수세 소멸"); sell_score += 1

    if prev_ma5 > prev_ma20 and curr_ma5 < curr_ma20:
        sell_signals.append("MA 데드크로스 - 중기 하락 전환"); sell_score += 2

    if curr_close < curr_ma20 and curr_close < curr_ma5:
        sell_signals.append("이동평균선 아래 위치 - 하락 추세"); sell_score += 1

    return buy_score, buy_signals, sell_score, sell_signals

def final_judgment(buy_score, sell_score):
    if buy_score == 0 and sell_score == 0:
        return "[중립] 관망", "gray", "중립"
    if buy_score > sell_score:
        if buy_score >= 6:   label = "매우 강한 매수"
        elif buy_score >= 4: label = "강한 매수"
        elif buy_score >= 2: label = "중간 매수"
        else:                label = "약한 매수"
        return f"[매수] {label}", "blue", f"[매수] {label}"
    if sell_score > buy_score:
        if sell_score >= 6:   label = "매우 강한 매도"
        elif sell_score >= 4: label = "강한 매도"
        elif sell_score >= 2: label = "중간 매도"
        else:                 label = "약한 매도"
        return f"[매도] {label}", "red", f"[매도] {label}"
    return "[중립] 균형", "gray", "균형"

# ==========================================
# 5. 장 상태
# ==========================================
def get_market_status():
    et      = datetime.datetime.now(pytz.timezone('America/New_York'))
    et_hour = et.hour + et.minute / 60
    if et.weekday() < 5 and 9.5 <= et_hour < 16:
        return "[장중] 미국 시장 거래 중", True
    elif et.weekday() < 5 and (4 <= et_hour < 9.5 or 16 <= et_hour < 20):
        return "[시간외] 프리/애프터 마켓", False
    return "[마감] 미국 시장 종료", False

# ==========================================
# 6. 분석 + 차트
# ==========================================
def analyze(ticker, mode='기본'):
    cfg       = MODE_CONFIG[mode]
    bar_width = cfg['bar_width']
    label     = cfg['label']

    df = get_df(ticker, mode)
    if df is None or df.empty:
        return None, None

    df = calc_indicators(df)

    curr  = get_value(df['Close'])
    rsi   = get_value(df['RSI'])
    upper = get_value(df['Upper'])
    lower = get_value(df['Lower'])
    vol   = get_value(df['Volume'])
    macd  = get_value(df['MACD'])
    sk    = get_value(df['Stoch_K'])
    ma5   = get_value(df['MA5'])
    ma20  = get_value(df['MA20'])

    now_str      = df.index[-1].strftime('%Y-%m-%d') if mode == '기본' else str(df.index[-1])[:16]
    kt_str       = datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M (KST)')
    market, _    = get_market_status()
    target_price = curr * 1.05
    stop_loss    = curr * 0.97

    buy_score, buy_signals, sell_score, sell_signals = detect_signal(df)
    judgment, _, chart_title = final_judgment(buy_score, sell_score)

    buy_text  = "\n".join([f"[매수] {s}" for s in buy_signals])  or "없음"
    sell_text = "\n".join([f"[매도] {s}" for s in sell_signals]) or "없음"

    if '매수' in judgment:   action = "*매수 타이밍* - 분할 매수 고려 (한 번에 전부 X)"
    elif '매도' in judgment: action = "*매도 타이밍* - 분할 매도 고려 (익절/손절 확인)"
    else:                    action = "*관망 타이밍* - 신호 확인될 때까지 대기"

    report = (
        f"*[{ticker}] {label} 분석 리포트*\n"
        f"기준: {now_str} | 조회: {kt_str}\n"
        f"{market}\n"
        f"--------------------\n"
        f"현재가: *{curr:.2f}* | 목표가: {target_price:.2f} | 손절가: {stop_loss:.2f}\n"
        f"거래량: {vol:,.0f}\n"
        f"RSI: {rsi:.1f} | MACD: {macd:.3f} | Stoch K: {sk:.1f}\n"
        f"MA5: {ma5:.2f} | MA20: {ma20:.2f}\n"
        f"BB상단: {upper:.2f} | BB하단: {lower:.2f}\n\n"
        f"--------------------\n"
        f"*매수 신호 ({buy_score}점)*\n{buy_text}\n\n"
        f"*매도 신호 ({sell_score}점)*\n{sell_text}\n\n"
        f"--------------------\n"
        f"최종 판정: *{judgment}*\n{action}"
    )

    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(14, 18), sharex=True)

    ax1.plot(df.index, df['Close'], color='black', label='Price',    linewidth=1.5, zorder=3)
    ax1.plot(df.index, df['MA5'],   color='orange', label='MA5',     linewidth=1.0, linestyle='--')
    ax1.plot(df.index, df['MA20'],  color='blue',   label='MA20',    linewidth=1.0, linestyle='--')
    ax1.plot(df.index, df['Upper'], color='red',    label='BB Upper', alpha=0.4, linewidth=1)
    ax1.plot(df.index, df['Lower'], color='blue',   label='BB Lower', alpha=0.4, linewidth=1)
    ax1.fill_between(df.index, df['Lower'].values.flatten(), df['Upper'].values.flatten(), color='gray', alpha=0.1)
    ax1.axhline(target_price, color='green', linestyle='--', alpha=0.6, linewidth=1.2, label=f'Target {target_price:.2f}')
    ax1.axhline(stop_loss,    color='red',   linestyle='--', alpha=0.6, linewidth=1.2, label=f'Stop {stop_loss:.2f}')

    for idx, val, color, fc, offset, txt in [
        (df['High'].idxmax(), float(df['High'].max()), 'red',  '#ffebee', 14,  f'High {float(df["High"].max()):.2f}'),
        (df['Low'].idxmin(),  float(df['Low'].min()),  'blue', '#e3f2fd', -20, f'Low {float(df["Low"].min()):.2f}'),
    ]:
        ax1.scatter(idx, val, color=color, marker='*', s=250, zorder=5)
        ax1.annotate(txt, xy=(idx, val), xytext=(0, offset), textcoords='offset points',
                     ha='center', fontsize=9, fontweight='bold', color=color,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor=fc, edgecolor=color, alpha=0.9))

    if buy_score > sell_score and buy_score > 0: ax1.set_facecolor('#e8f5e9')
    elif sell_score > buy_score:                 ax1.set_facecolor('#ffebee')
    ax1.set_title(f"{ticker} [{label}] - {chart_title} | {now_str} | {market}", fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=7, ncol=3)
    ax1.grid(True, alpha=0.2)

    bar_colors = np.where(df['Close'] >= df['Open'], 'red', 'blue').flatten()
    ax2.bar(df.index, df['Volume'].values.flatten(), color=bar_colors, alpha=0.7, width=bar_width)
    ax2.plot(df.index, df['Volume'].rolling(20).mean(), color='orange', linewidth=1.2, linestyle='--', label='Volume 20MA')
    ax2.set_ylabel('Volume'); ax2.legend(loc='upper left', fontsize=8); ax2.grid(True, alpha=0.2)

    ax3.plot(df.index, df['RSI'], color='purple', label='RSI (14)', linewidth=1.5)
    ax3.axhline(70, color='red',  linestyle='--', alpha=0.5, label='Overbought(70)')
    ax3.axhline(50, color='gray', linestyle=':',  alpha=0.4)
    ax3.axhline(30, color='blue', linestyle='--', alpha=0.5, label='Oversold(30)')
    ax3.fill_between(df.index, 70, 100, where=(df['RSI'] >= 70), color='red',  alpha=0.15)
    ax3.fill_between(df.index,  0,  30, where=(df['RSI'] <= 30), color='blue', alpha=0.15)
    ax3.scatter(df.index[-1], rsi, color='purple', zorder=5, s=80)
    ax3.annotate(f'  {rsi:.1f}', xy=(df.index[-1], rsi), color='purple', fontweight='bold', fontsize=10)
    ax3.set_ylim(0, 100); ax3.set_ylabel('RSI'); ax3.legend(loc='upper left', fontsize=8); ax3.grid(True, alpha=0.2)

    ax4.plot(df.index, df['MACD'],        color='blue',   label='MACD',   linewidth=1.2)
    ax4.plot(df.index, df['MACD_signal'], color='orange', label='Signal', linewidth=1.2)
    hist_colors = np.where(df['MACD_hist'] >= 0, 'red', 'blue').flatten()
    ax4.bar(df.index, df['MACD_hist'].values.flatten(), color=hist_colors, alpha=0.4, width=bar_width, label='Histogram')
    ax4.axhline(0, color='gray', linestyle='--', alpha=0.4)
    ax4.set_ylabel('MACD'); ax4.legend(loc='upper left', fontsize=8); ax4.grid(True, alpha=0.2)

    ax5.plot(df.index, df['Stoch_K'], color='green', label='%K', linewidth=1.2)
    ax5.plot(df.index, df['Stoch_D'], color='red',   label='%D', linewidth=1.2)
    ax5.axhline(80, color='red',  linestyle='--', alpha=0.5, label='Overbought(80)')
    ax5.axhline(20, color='blue', linestyle='--', alpha=0.5, label='Oversold(20)')
    ax5.fill_between(df.index, 80, 100, where=(df['Stoch_K'] >= 80), color='red',  alpha=0.15)
    ax5.fill_between(df.index,  0,  20, where=(df['Stoch_K'] <= 20), color='blue', alpha=0.15)
    ax5.set_ylim(0, 100); ax5.set_ylabel('Stochastic'); ax5.legend(loc='upper left', fontsize=8); ax5.grid(True, alpha=0.2)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return report, buf

# ==========================================
# 7. 텔레그램 핸들러
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts  = update.message.text.strip().upper().split()
    ticker = parts[0]
    mode   = '기본'

    if len(parts) >= 2:
        if parts[1] in ['단타', '5M', '5분']:    mode = '단타'
        elif parts[1] in ['스윙', '1H', '1시간']: mode = '스윙'

    await update.message.reply_text(f"[분석 중] {ticker} [{MODE_CONFIG[mode]['label']}] 잠시만 기다려주세요.")

    report, chart_buf = analyze(ticker, mode)

    if report is None:
        await update.message.reply_text(
            f"[오류] {ticker} 데이터를 가져오지 못했습니다.\n"
            f"입력: AAPL / AAPL 단타 / AAPL 스윙"
        )
        return

    await update.message.reply_text(report, parse_mode='Markdown')
    await update.message.reply_photo(
        photo=chart_buf,
        read_timeout=60, write_timeout=60, connect_timeout=60, pool_timeout=60,
        caption=f"{ticker} {MODE_CONFIG[mode]['label']} 차트"
    )

# ==========================================
# 8. 나스닥 티커 + 세력 감지 + 급등 스캔
# ==========================================
def get_nasdaq_tickers():
    url     = "https://raw.githubusercontent.com/datasets/nasdaq-listings/master/data/nasdaq-listed-symbols.csv"
    tickers = [t for t in pd.read_csv(url)["Symbol"].dropna() if str(t).isalpha() and len(t) <= 5]
    random.shuffle(tickers)
    return tickers[:200]

def detect_smart_money(df):
    score, signals = 0, []
    try:
        avg_vol      = float(df['Volume'].rolling(20).mean().iloc[-1])
        curr_vol     = float(df['Volume'].iloc[-1])
        vol_ratio    = curr_vol / avg_vol if avg_vol > 0 else 0
        curr_close   = float(df['Close'].iloc[-1])
        prev_close   = float(df['Close'].iloc[-2])
        price_change = (curr_close - prev_close) / prev_close * 100

        if vol_ratio >= 5:
            score += 3; signals.append(f"거래량 {vol_ratio:.1f}배 - 세력 강한 의심")
        elif vol_ratio >= 3:
            score += 2; signals.append(f"거래량 {vol_ratio:.1f}배 - 세력 의심")

        if curr_close > float(df['Close'].rolling(20).max().iloc[-2]):
            score += 2; signals.append("20일 고점 돌파")

        if vol_ratio >= 3 and price_change < 2:
            score += 3; signals.append("거래량 대비 가격 낮음 - 매집 의심")

        if len(df) >= 3:
            last3 = df['Close'].iloc[-3:].values.flatten()
            if last3[0] < last3[1] < last3[2]:
                score += 1; signals.append("3연속 양봉")

        et_hour = datetime.datetime.now(pytz.timezone('America/New_York')).hour
        if 9 <= et_hour <= 10 or 15 <= et_hour <= 16:
            score += 1; signals.append("세력 주요 활동 시간대")

    except Exception as e:
        print(f"세력 감지 오류: {e}")
    return score, signals

def find_surge_stocks():
    surged = []

    for ticker in get_nasdaq_tickers():
        try:
            data = yf.download(ticker, period="5d", interval="5m", progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            if len(data) < 20:
                continue

            change = (float(data['Close'].iloc[-1]) - float(data['Close'].iloc[0])) / float(data['Close'].iloc[0]) * 100
            if change < 2:
                continue

            curr_price = float(data['Close'].iloc[-1])
            print(f"{ticker}: {change:.2f}%")

            try:
                buy_5m, _, sell_5m, _ = detect_signal(calc_indicators(data.copy()))
            except:
                buy_5m, sell_5m = 0, 0

            try:
                d1 = yf.download(ticker, period="6mo", interval="1d", progress=False)
                if isinstance(d1.columns, pd.MultiIndex): d1.columns = d1.columns.droplevel(1)
                buy_1d, _, sell_1d, _ = detect_signal(calc_indicators(d1)) if not d1.empty else (0, [], 0, [])
            except:
                buy_1d, sell_1d = 0, 0

            smart_score, _ = detect_smart_money(data)
            total_score    = buy_5m + buy_1d + smart_score

            surged.append((ticker, change, curr_price, buy_5m, sell_5m, buy_1d, sell_1d, smart_score, total_score))

        except Exception as e:
            print(f"{ticker} 오류: {e}")

    surged.sort(key=lambda x: x[8], reverse=True)

    result = []
    for i, (ticker, change, _, buy_5m, sell_5m, buy_1d, sell_1d, smart_score, total_score) in enumerate(surged[:10], 1):
        if total_score >= 8:   overall = "강력 매수"
        elif total_score >= 5: overall = "매수 고려"
        elif total_score >= 3: overall = "관망"
        else:                  overall = "주의"

        smart_label = "[세력 강한 의심]" if smart_score >= 5 else "[세력 의심]" if smart_score >= 3 else ""
        result.append(f"{i}. {ticker} +{change:.2f}% | 총점:{total_score} | {overall} {smart_label}".strip())

    return result

# ==========================================
# 9. 자동 스캔 루프
# ==========================================
async def auto_surge_loop(app):
    await asyncio.sleep(10)
    while True:
        _, is_open = get_market_status()
        if is_open and CHAT_ID:
            print("장중 - 스캔 시작")
            surged = find_surge_stocks()
            print(f"감지 종목 수: {len(surged)}")
            if surged:
                try:
                    await app.bot.send_message(
                        chat_id=int(CHAT_ID),
                        text="나스닥 선제 급등 감지\n\n" + "\n".join(surged)
                    )
                    print("전송 완료")
                except Exception as e:
                    print(f"전송 오류: {e}")
        else:
            print("장 마감 - 스캔 스킵")

        await asyncio.sleep(180)

async def error_handler(update, context):
    print(f"에러: {context.error}")

# ==========================================
# 10. 봇 실행
# ==========================================
def main():
    print("텔레그램 봇 시작!")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # ✅ 태스크 참조 저장해서 정상 종료
    surge_task = None

    async def start_background(app):
        nonlocal surge_task
        surge_task = asyncio.create_task(auto_surge_loop(app))

    async def stop_background(app):
        nonlocal surge_task
        if surge_task and not surge_task.done():
            surge_task.cancel()
            try:
                await surge_task
            except asyncio.CancelledError:
                pass
        print("백그라운드 태스크 종료")

    app.post_init  = start_background
    app.post_stop  = stop_background  # ✅ 종료 시 정리
    app.run_polling()

if __name__ == "__main__":
    main()
