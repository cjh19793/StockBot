import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import platform
import io
import os

from telegram import Update, ReplyKeyboardMarkup
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
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# 모드별 설정
MODE_CONFIG = {
    '단타': {
        'interval': '5m',
        'period'  : '5d',
        'label'   : '5분봉 (단타)',
        'bar_width': 0.003,
    },
    '스윙': {
        'interval': '1h',
        'period'  : '60d',
        'label'   : '1시간봉 (스윙)',
        'bar_width': 0.03,
    },
    '기본': {
        'interval': '1d',
        'period'  : '6mo',
        'label'   : '일봉 (기본)',
        'bar_width': 0.6,
    },
}

# ==========================================
# 2. 데이터 가져오기
# ==========================================
def get_df(ticker, mode='기본'):
    try:
        cfg = MODE_CONFIG[mode]
        df = yf.download(
            ticker,
            period=cfg['period'],
            interval=cfg['interval'],
            progress=False
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        if df.empty:
            return None
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
    df['MA20']   = df['Close'].rolling(window=20).mean()
    df['stddev'] = df['Close'].rolling(window=20).std()
    df['Upper']  = df['MA20'] + (df['stddev'] * 2)
    df['Lower']  = df['MA20'] - (df['stddev'] * 2)

    delta = df['Close'].diff()
    gain  = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD']        = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist']   = df['MACD'] - df['MACD_signal']

    low14  = df['Low'].rolling(window=14).min()
    high14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * (df['Close'] - low14) / (high14 - low14)
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

    df['MA5']  = df['Close'].rolling(window=5).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()

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
    curr_ma20   = get_value(df['MA20'])
    curr_ma5    = get_value(df['MA5'])
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

    prev_ma5  = get_value(df['MA5'].iloc[:-1])
    prev_ma20 = get_value(df['MA20'].iloc[:-1])

    # ── 매수 조건 ──────────────────────────────────────
    if curr_rsi <= 30:
        buy_signals.append(f"RSI 과매도 ({curr_rsi:.1f}) — 반등 가능성 높음")
        buy_score += 1
    elif curr_rsi <= 40:
        buy_signals.append(f"RSI 저점 근접 ({curr_rsi:.1f}) — 약한 매수 구간")
        buy_score += 1

    if curr_close <= curr_lower:
        buy_signals.append(f"볼린저 하단 이탈 ({curr_lower:.2f}) — 단기 반등 기대")
        buy_score += 1
    elif curr_close <= curr_lower * 1.02:
        buy_signals.append(f"볼린저 하단 근접 ({curr_lower:.2f}) — 지지선 테스트")
        buy_score += 1

    if prev_macd < prev_macd_signal and macd > macd_signal:
        buy_signals.append("MACD 골든크로스 — 상승 전환 신호")
        buy_score += 2

    if prev_stoch_k < prev_stoch_d and stoch_k > stoch_d and stoch_k < 20:
        buy_signals.append(f"스토캐스틱 골든크로스 ({stoch_k:.1f}) — 과매도 반등")
        buy_score += 1

    if avg_volume > 0 and curr_volume >= avg_volume * 2.0:
        buy_signals.append(f"거래량 폭증 ({curr_volume/avg_volume:.1f}배) — 강한 매수세")
        buy_score += 2
    elif avg_volume > 0 and curr_volume >= avg_volume * 1.5:
        buy_signals.append(f"거래량 급증 ({curr_volume/avg_volume:.1f}배) — 매수세 증가")
        buy_score += 1

    if prev_ma5 < prev_ma20 and curr_ma5 > curr_ma20:
        buy_signals.append("MA 골든크로스 (5일선↑20일선) — 중기 상승 전환")
        buy_score += 2

    if curr_close > curr_ma20 and curr_close > curr_ma5:
        buy_signals.append("이동평균선 위 안착 — 상승 추세 유지")
        buy_score += 1

    # ── 매도 조건 ──────────────────────────────────────
    if curr_rsi >= 70:
        sell_signals.append(f"RSI 과매수 ({curr_rsi:.1f}) — 조정 가능성 높음")
        sell_score += 1
    elif curr_rsi >= 60:
        sell_signals.append(f"RSI 고점 근접 ({curr_rsi:.1f}) — 약한 매도 구간")
        sell_score += 1

    if curr_close >= curr_upper:
        sell_signals.append(f"볼린저 상단 이탈 ({curr_upper:.2f}) — 단기 조정 가능")
        sell_score += 1
    elif curr_close >= curr_upper * 0.98:
        sell_signals.append(f"볼린저 상단 근접 ({curr_upper:.2f}) — 저항선 테스트")
        sell_score += 1

    if prev_macd > prev_macd_signal and macd < macd_signal:
        sell_signals.append("MACD 데드크로스 — 하락 전환 신호")
        sell_score += 2

    if prev_stoch_k > prev_stoch_d and stoch_k < stoch_d and stoch_k > 80:
        sell_signals.append(f"스토캐스틱 데드크로스 ({stoch_k:.1f}) — 과매수 하락")
        sell_score += 1

    if avg_volume > 0 and curr_volume < avg_volume * 0.5:
        sell_signals.append(f"거래량 급감 (평균의 {curr_volume/avg_volume:.1f}배) — 매수세 소멸")
        sell_score += 1

    if prev_ma5 > prev_ma20 and curr_ma5 < curr_ma20:
        sell_signals.append("MA 데드크로스 (5일선↓20일선) — 중기 하락 전환")
        sell_score += 2

    if curr_close < curr_ma20 and curr_close < curr_ma5:
        sell_signals.append("이동평균선 아래 위치 — 하락 추세 진행")
        sell_score += 1

    return buy_score, buy_signals, sell_score, sell_signals


def final_judgment(buy_score, sell_score):
    if buy_score == 0 and sell_score == 0:
        return "⚖️ 중립 — 관망", "gray", "중립 — 관망"
    if buy_score > sell_score:
        if buy_score >= 6:   label = "매우 강한 매수!"
        elif buy_score >= 4: label = "강한 매수"
        elif buy_score >= 2: label = "중간 매수"
        else:                label = "약한 매수"
        return f"📈 {label}", "blue", f"[매수] {label}"
    if sell_score > buy_score:
        if sell_score >= 6:   label = "매우 강한 매도!"
        elif sell_score >= 4: label = "강한 매도"
        elif sell_score >= 2: label = "중간 매도"
        else:                 label = "약한 매도"
        return f"📉 {label}", "red", f"[매도] {label}"
    return "⚖️ 균형 — 관망", "gray", "균형 — 관망"

# ==========================================
# 5. 분석 + 차트 생성
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

    # 단타/스윙은 시분까지 표시
    if mode == '기본':
        now_str = df.index[-1].strftime('%Y-%m-%d')
    else:
        try:
            now_str = df.index[-1].strftime('%Y-%m-%d %H:%M')
        except:
            now_str = str(df.index[-1])[:16]

    buy_score, buy_signals, sell_score, sell_signals = detect_signal(df)
    judgment, j_color, chart_title = final_judgment(buy_score, sell_score)

    buy_text  = "\n".join([f"✅ {s}" for s in buy_signals])  if buy_signals  else "없음"
    sell_text = "\n".join([f"❌ {s}" for s in sell_signals]) if sell_signals else "없음"

    if '매수' in judgment:
        action_guide = "💡 *매수 타이밍*: 분할 매수 고려 (한 번에 전부 X)"
    elif '매도' in judgment:
        action_guide = "💡 *매도 타이밍*: 분할 매도 고려 (익절/손절 기준 확인)"
    else:
        action_guide = "💡 *관망 타이밍*: 신호 확인될 때까지 대기"

    # 목표가 / 손절가 자동 계산
    target_price = curr * 1.05   # +5%
    stop_loss    = curr * 0.97   # -3%

    report = (
        f"🚀 *[{ticker}] {label} 분석 리포트*\n"
        f"🕐 기준: {now_str}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 현재가: *{curr:.2f}*\n"
        f"🎯 목표가: {target_price:.2f} (+5%)\n"
        f"🛑 손절가: {stop_loss:.2f} (-3%)\n"
        f"📊 거래량: {vol:,.0f}\n"
        f"📈 RSI: {rsi:.1f} | MACD: {macd:.3f} | Stoch K: {sk:.1f}\n"
        f"📉 MA5: {ma5:.2f} | MA20: {ma20:.2f}\n"
        f"🏢 BB상단: {upper:.2f} | 🏠 BB하단: {lower:.2f}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📈 *매수 신호 ({buy_score}점)*\n{buy_text}\n\n"
        f"📉 *매도 신호 ({sell_score}점)*\n{sell_text}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎯 최종 판정: *{judgment}*\n"
        f"{action_guide}"
    )

    # ── 차트 생성 ───────────────────────────────────────
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(14, 18), sharex=True)

    # (1) 주가 + 볼린저밴드 + 이동평균
    ax1.plot(df.index, df['Close'], color='black', label='Price', linewidth=1.5, zorder=3)
    ax1.plot(df.index, df['MA5'],  color='orange', label='MA5',  linewidth=1.0, linestyle='--')
    ax1.plot(df.index, df['MA20'], color='blue',   label='MA20', linewidth=1.0, linestyle='--')
    ax1.plot(df.index, df['Upper'], color='red',  alpha=0.4, label='BB 상단', linewidth=1)
    ax1.plot(df.index, df['Lower'], color='blue', alpha=0.4, label='BB 하단', linewidth=1)
    ax1.fill_between(df.index,
                     df['Lower'].values.flatten(),
                     df['Upper'].values.flatten(),
                     color='gray', alpha=0.1)

    # 최고가 / 최저가 마커
    high_idx = df['High'].idxmax()
    low_idx  = df['Low'].idxmin()
    high_val = float(df['High'].max())
    low_val  = float(df['Low'].min())

    ax1.scatter(high_idx, high_val, color='red', marker='*', s=250, zorder=5, label=f'최고가 {high_val:.2f}')
    ax1.annotate(
        f'▲ 최고 {high_val:.2f}',
        xy=(high_idx, high_val),
        xytext=(0, 14), textcoords='offset points',
        ha='center', fontsize=9, fontweight='bold', color='red',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffebee', edgecolor='red', alpha=0.9)
    )
    ax1.scatter(low_idx, low_val, color='blue', marker='*', s=250, zorder=5, label=f'최저가 {low_val:.2f}')
    ax1.annotate(
        f'▼ 최저 {low_val:.2f}',
        xy=(low_idx, low_val),
        xytext=(0, -20), textcoords='offset points',
        ha='center', fontsize=9, fontweight='bold', color='blue',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#e3f2fd', edgecolor='blue', alpha=0.9)
    )

    # 목표가 / 손절가 수평선
    ax1.axhline(target_price, color='green', linestyle='--', alpha=0.6, linewidth=1.2, label=f'목표가 {target_price:.2f}')
    ax1.axhline(stop_loss,    color='red',   linestyle='--', alpha=0.6, linewidth=1.2, label=f'손절가 {stop_loss:.2f}')

    if buy_score > sell_score and buy_score > 0:
        ax1.set_facecolor('#e8f5e9')
    elif sell_score > buy_score:
        ax1.set_facecolor('#ffebee')

    ax1.set_title(f"{ticker} [{label}] — {chart_title} | {now_str}", fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=7, ncol=3)
    ax1.grid(True, alpha=0.2)

    # (2) 거래량
    bar_colors = np.where(df['Close'] >= df['Open'], 'red', 'blue').flatten()
    ax2.bar(df.index, df['Volume'].values.flatten(), color=bar_colors, alpha=0.7, width=bar_width)
    ax2.plot(df.index, df['Volume'].rolling(20).mean(),
             color='orange', linewidth=1.2, linestyle='--', label='거래량 20MA')
    ax2.set_ylabel('Volume')
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.2)

    # (3) RSI
    ax3.plot(df.index, df['RSI'], color='purple', label='RSI (14)', linewidth=1.5)
    ax3.axhline(70, color='red',  linestyle='--', alpha=0.5, label='과매수(70) → 매도 고려')
    ax3.axhline(50, color='gray', linestyle=':',  alpha=0.4)
    ax3.axhline(30, color='blue', linestyle='--', alpha=0.5, label='과매도(30) → 매수 고려')
    ax3.fill_between(df.index, 70, 100, where=(df['RSI'] >= 70), color='red',  alpha=0.15)
    ax3.fill_between(df.index,  0,  30, where=(df['RSI'] <= 30), color='blue', alpha=0.15)
    ax3.scatter(df.index[-1], rsi, color='purple', zorder=5, s=80)
    ax3.annotate(f'  {rsi:.1f}', xy=(df.index[-1], rsi),
                 color='purple', fontweight='bold', fontsize=10)
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
    ax5.axhline(80, color='red',  linestyle='--', alpha=0.5, label='과매수(80) → 매도 고려')
    ax5.axhline(20, color='blue', linestyle='--', alpha=0.5, label='과매도(20) → 매수 고려')
    ax5.fill_between(df.index, 80, 100, where=(df['Stoch_K'] >= 80), color='red',  alpha=0.15)
    ax5.fill_between(df.index,  0,  20, where=(df['Stoch_K'] <= 20), color='blue', alpha=0.15)
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
    text   = update.message.text.strip().upper()
    parts  = text.split()
    ticker = parts[0]

    # 모드 파싱
    if len(parts) >= 2:
        mode_input = parts[1]
        if mode_input in ['단타', '5M', '5분']:
            mode = '단타'
        elif mode_input in ['스윙', '1H', '1시간']:
            mode = '스윙'
        else:
            mode = '기본'
    else:
        mode = '기본'

    cfg = MODE_CONFIG[mode]
    await update.message.reply_text(
        f"🔍 {ticker} [{cfg['label']}] 분석 중... 잠시만 기다려주세요!"
    )

    report, chart_buf = analyze(ticker, mode)

    if report is None:
        await update.message.reply_text(
            f"❌ {ticker} 데이터를 가져오지 못했습니다.\n"
            f"미국 주식 티커를 확인해주세요. (예: AAPL, TSLA, NVDA)\n\n"
            f"입력 방법:\n"
            f"AAPL        → 일봉 (기본)\n"
            f"AAPL 단타   → 5분봉\n"
            f"AAPL 스윙   → 1시간봉"
        )
        return

    await update.message.reply_text(report, parse_mode='Markdown')
    await update.message.reply_photo(
        photo=chart_buf,
        caption=f"📊 {ticker} {cfg['label']} 차트"
    )

# ==========================================
# 7. 봇 실행
# ==========================================
if __name__ == "__main__":
    print("🤖 텔레그램 봇 시작!")
    print("입력 방법: AAPL / AAPL 단타 / AAPL 스윙")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
