import finnhub
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
import platform
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ── 한글 폰트 설정 ──────────────────────────
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 설정
# ==========================================
TELEGRAM_TOKEN = '8461695506:AAEnh1QdWuRsztWIx9_uIr59u0lA8uvshXg'
FINNHUB_KEY    = 'd7oqrfpr01qmthud7v5gd7oqrfpr01qmthud7v60'

# ==========================================
# 2. Finnhub 데이터 가져오기
# ==========================================
def get_df_from_finnhub(ticker):
    client = finnhub.Client(api_key=FINNHUB_KEY)

    end   = int(time.time())
    start = end - 60 * 60 * 24 * 365  # 24시간치 1분봉

    candles = client.stock_candles(ticker, 'D', start, end)

    if candles['s'] != 'ok':
        return None

    df = pd.DataFrame({
        'Open'  : candles['o'],
        'High'  : candles['h'],
        'Low'   : candles['l'],
        'Close' : candles['c'],
        'Volume': candles['v'],
    }, index=pd.to_datetime(candles['t'], unit='s'))

    df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
    return df

# ==========================================
# 3. 지표 계산
# ==========================================
def get_value(series):
    return float(np.array(series).flatten()[-1])

def calc_indicators(df):
    # 볼린저 밴드
    df['MA20']   = df['Close'].rolling(window=20).mean()
    df['stddev'] = df['Close'].rolling(window=20).std()
    df['Upper']  = df['MA20'] + (df['stddev'] * 2)
    df['Lower']  = df['MA20'] - (df['stddev'] * 2)

    # RSI
    delta = df['Close'].diff()
    gain  = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD']        = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist']   = df['MACD'] - df['MACD_signal']

    # 스토캐스틱
    low14  = df['Low'].rolling(window=14).min()
    high14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * (df['Close'] - low14) / (high14 - low14)
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

    return df

# ==========================================
# 4. 매수/매도 신호 감지
# ==========================================
def detect_signal(df):
    buy_signals, sell_signals = [], []
    buy_score, sell_score = 0, 0

    curr_close  = get_value(df['Close'])
    curr_rsi    = get_value(df['RSI'])
    curr_upper  = get_value(df['Upper'])
    curr_lower  = get_value(df['Lower'])
    curr_volume = get_value(df['Volume'])
    avg_volume  = get_value(df['Volume'].rolling(window=20).mean().dropna())

    macd             = get_value(df['MACD'])
    macd_signal      = get_value(df['MACD_signal'])
    prev_macd        = get_value(df['MACD'].iloc[:-1])
    prev_macd_signal = get_value(df['MACD_signal'].iloc[:-1])

    stoch_k      = get_value(df['Stoch_K'])
    stoch_d      = get_value(df['Stoch_D'])
    prev_stoch_k = get_value(df['Stoch_K'].iloc[:-1])
    prev_stoch_d = get_value(df['Stoch_D'].iloc[:-1])

    # ── 매수 조건 ──────────────────────────────────────
    if curr_rsi <= 30:
        buy_signals.append(f"RSI {curr_rsi:.1f} → 과매도")
        buy_score += 1
    if curr_close <= curr_lower:
        buy_signals.append(f"볼린저 하단 터치({curr_lower:.2f})")
        buy_score += 1
    if prev_macd < prev_macd_signal and macd > macd_signal:
        buy_signals.append("MACD 골든크로스")
        buy_score += 1
    if prev_stoch_k < prev_stoch_d and stoch_k > stoch_d and stoch_k < 20:
        buy_signals.append("스토캐스틱 골든크로스")
        buy_score += 1
    if avg_volume > 0 and curr_volume >= avg_volume * 1.5:
        buy_signals.append(f"거래량 {curr_volume/avg_volume:.1f}배 급증")
        buy_score += 1

    # ── 매도 조건 ──────────────────────────────────────
    if curr_rsi >= 70:
        sell_signals.append(f"RSI {curr_rsi:.1f} → 과매수")
        sell_score += 1
    if curr_close >= curr_upper:
        sell_signals.append(f"볼린저 상단 터치({curr_upper:.2f})")
        sell_score += 1
    if prev_macd > prev_macd_signal and macd < macd_signal:
        sell_signals.append("MACD 데드크로스")
        sell_score += 1
    if prev_stoch_k > prev_stoch_d and stoch_k < stoch_d and stoch_k > 80:
        sell_signals.append("스토캐스틱 데드크로스")
        sell_score += 1
    if avg_volume > 0 and curr_volume < avg_volume * 0.5:
        sell_signals.append(f"거래량 급감 (평균의 {curr_volume/avg_volume:.1f}배)")
        sell_score += 1

    return buy_score, buy_signals, sell_score, sell_signals


def final_judgment(buy_score, sell_score):
    if buy_score == 0 and sell_score == 0:
        return "⚖️ 중립 — 관망", "gray", "중립 — 관망"
    if buy_score > sell_score:
        labels = {1: "약한 매수", 2: "중간 매수", 3: "강한 매수"}
        label  = labels.get(buy_score, "매우 강한 매수!")
        return f"📈 {label}", "blue", f"[매수] {label}"
    if sell_score > buy_score:
        labels = {1: "약한 매도", 2: "중간 매도", 3: "강한 매도"}
        label  = labels.get(sell_score, "매우 강한 매도!")
        return f"📉 {label}", "red", f"[매도] {label}"
    return "⚖️ 균형 — 관망", "gray", "균형 — 관망"

# ==========================================
# 5. 분석 + 차트 생성
# ==========================================
def analyze(ticker):
    bar_width = 0.0003  # 1분봉에 맞게 조정

    df = get_df_from_finnhub(ticker)
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

    # 현재 시각 표시용
    now_str = df.index[-1].strftime('%Y-%m-%d %H:%M (ET)')

    buy_score, buy_signals, sell_score, sell_signals = detect_signal(df)
    judgment, j_color, chart_title = final_judgment(buy_score, sell_score)

    # ── 텔레그램 텍스트 리포트 ──────────────────────────
    buy_text  = "\n".join([f"✅ {s}" for s in buy_signals])  if buy_signals  else "없음"
    sell_text = "\n".join([f"❌ {s}" for s in sell_signals]) if sell_signals else "없음"
    report = (
        f"🚀 *[{ticker}] 분석 리포트*\n"
        f"🕐 기준 시각: {now_str}\n"
        f"💰 현재가: {curr:.2f}\n"
        f"📊 거래량: {vol:,.0f}\n"
        f"📈 RSI: {rsi:.1f} | MACD: {macd:.3f} | Stoch K: {sk:.1f}\n"
        f"🏢 BB상단: {upper:.2f} | 🏠 하단: {lower:.2f}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📈 *매수 신호*\n{buy_text}\n\n"
        f"📉 *매도 신호*\n{sell_text}\n\n"
        f"최종 판정: *{judgment}*"
    )

    # ── 차트 생성 ───────────────────────────────────────
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(14, 18), sharex=True)

    # (1) 주가 + 볼린저밴드
    ax1.plot(df.index, df['Close'], color='black', label='Price', linewidth=1.5)
    ax1.plot(df.index, df['Upper'], color='red',  alpha=0.4, label='BB 상단', linewidth=1)
    ax1.plot(df.index, df['Lower'], color='blue', alpha=0.4, label='BB 하단', linewidth=1)
    ax1.fill_between(df.index,
                     df['Lower'].values.flatten(),
                     df['Upper'].values.flatten(),
                     color='gray', alpha=0.1)
    if buy_score >= sell_score and buy_score > 0:
        ax1.set_facecolor('#e8f5e9')
    elif sell_score > buy_score:
        ax1.set_facecolor('#ffebee')
    ax1.set_title(f"{ticker} [1m] — {chart_title} | {now_str}", fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.2)

    # (2) 거래량
    bar_colors = np.where(df['Close'] >= df['Open'], 'red', 'blue').flatten()
    ax2.bar(df.index, df['Volume'].values.flatten(),
            color=bar_colors, alpha=0.7, width=bar_width)
    ax2.plot(df.index, df['Volume'].rolling(20).mean(),
             color='orange', linewidth=1.2, linestyle='--', label='거래량 20MA')
    ax2.set_ylabel('Volume')
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.2)

    # (3) RSI
    ax3.plot(df.index, df['RSI'], color='purple', label='RSI (14)', linewidth=1.5)
    ax3.axhline(70, color='red',  linestyle='--', alpha=0.5, label='과매수(70)')
    ax3.axhline(50, color='gray', linestyle=':',  alpha=0.4)
    ax3.axhline(30, color='blue', linestyle='--', alpha=0.5, label='과매도(30)')
    ax3.fill_between(df.index, 70, 100, where=(df['RSI'] >= 70), color='red',  alpha=0.1)
    ax3.fill_between(df.index,  0,  30, where=(df['RSI'] <= 30), color='blue', alpha=0.1)
    ax3.scatter(df.index[-1], rsi, color='purple', zorder=5, s=60)
    ax3.annotate(f'  {rsi:.1f}', xy=(df.index[-1], rsi),
                 color='purple', fontweight='bold', fontsize=9)
    ax3.set_ylim(0, 100)
    ax3.set_ylabel('RSI')
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.2)

    # (4) MACD
    ax4.plot(df.index, df['MACD'],        color='blue',   label='MACD',   linewidth=1.2)
    ax4.plot(df.index, df['MACD_signal'], color='orange', label='Signal', linewidth=1.2)
    hist_colors = np.where(df['MACD_hist'] >= 0, 'red', 'blue').flatten()
    ax4.bar(df.index, df['MACD_hist'].values.flatten(),
            color=hist_colors, alpha=0.4, width=bar_width, label='Histogram')
    ax4.axhline(0, color='gray', linestyle='--', alpha=0.4)
    ax4.set_ylabel('MACD')
    ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, alpha=0.2)

    # (5) 스토캐스틱
    ax5.plot(df.index, df['Stoch_K'], color='green', label='%K', linewidth=1.2)
    ax5.plot(df.index, df['Stoch_D'], color='red',   label='%D', linewidth=1.2)
    ax5.axhline(80, color='red',  linestyle='--', alpha=0.5, label='과매수(80)')
    ax5.axhline(20, color='blue', linestyle='--', alpha=0.5, label='과매도(20)')
    ax5.fill_between(df.index, 80, 100, where=(df['Stoch_K'] >= 80), color='red',  alpha=0.1)
    ax5.fill_between(df.index,  0,  20, where=(df['Stoch_K'] <= 20), color='blue', alpha=0.1)
    ax5.set_ylim(0, 100)
    ax5.set_ylabel('Stochastic')
    ax5.legend(loc='upper left', fontsize=8)
    ax5.grid(True, alpha=0.2)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return report, buf

# ==========================================
# 6. 텔레그램 봇 핸들러
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = update.message.text.strip().upper()
    await update.message.reply_text(f"🔍 {ticker} 실시간 분석 중... 잠시만 기다려주세요!")

    report, chart_buf = analyze(ticker)

    if report is None:
        await update.message.reply_text(
            f"❌ {ticker} 데이터를 가져오지 못했습니다.\n"
            f"미국 주식 티커를 확인해주세요. (예: AAPL, TSLA, NVDA)"
        )
        return

    await update.message.reply_text(report, parse_mode='Markdown')
    await update.message.reply_photo(photo=chart_buf, caption=f"📊 {ticker} 실시간 차트")

# ==========================================
# 7. 봇 실행
# ==========================================
if __name__ == "__main__":
    print("🤖 텔레그램 봇 시작! 미국 주식 티커를 입력하세요. (예: AAPL, TSLA)")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()