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
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 설정
# ==========================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID        = os.environ.get('CHAT_ID')

MODE_CONFIG = {
    '단타': {'interval': '5m',  'period': '5d',  'label': '5min (Scalping)',  'bar_width': 0.003},
    '스윙': {'interval': '1h',  'period': '60d', 'label': '1hour (Swing)',    'bar_width': 0.03},
    '기본': {'interval': '1d',  'period': '6mo', 'label': 'Daily (Basic)',    'bar_width': 0.6},
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
        return "[Neutral] Watch", "gray", "Neutral"
    if buy_score > sell_score:
        if buy_score >= 6:   label = "Strong Buy"
        elif buy_score >= 4: label = "Buy"
        elif buy_score >= 2: label = "Weak Buy"
        else:                label = "Slight Buy"
        return f"[Buy] {label}", "blue", f"[Buy] {label}"
    if sell_score > buy_score:
        if sell_score >= 6:   label = "Strong Sell"
        elif sell_score >= 4: label = "Sell"
        elif sell_score >= 2: label = "Weak Sell"
        else:                 label = "Slight Sell"
        return f"[Sell] {label}", "red", f"[Sell] {label}"
    return "[Neutral] Balance", "gray", "Balance"

# ==========================================
# 5. 장 상태
# ==========================================
def get_market_status():
    et      = datetime.datetime.now(pytz.timezone('America/New_York'))
    et_hour = et.hour + et.minute / 60
    if et.weekday() < 5 and 9.5 <= et_hour < 16:
        return "[Open] US Market Trading", True
    elif et.weekday() < 5 and (4 <= et_hour < 9.5 or 16 <= et_hour < 20):
        return "[Extended] Pre/After Market", False
    return "[Closed] US Market Closed", False
# 실시간 현재가 가져오기
def get_realtime_price(ticker):
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        if df.empty:
            return None
        return float(df['Close'].iloc[-1])
    except:
        return None
# ==========================================
# 공포탐욕지수
# ==========================================
def get_fear_greed():
    try:
        # CNN Fear & Greed API
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        res = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://edition.cnn.com/'
        })
        data  = res.json()
        score = round(float(data['fear_and_greed']['score']))

        if score <= 25:   label = "극도의 공포 - 매수 기회"
        elif score <= 45: label = "공포 - 매수 고려"
        elif score <= 55: label = "중립"
        elif score <= 75: label = "탐욕 - 매도 고려"
        else:             label = "극도의 탐욕 - 매도 주의"

        return score, label

    except Exception as e:
        print(f"CNN 오류: {e}")

        # CNN 실패 시 alternative.me 백업
        try:
            res   = requests.get("https://api.alternative.me/fng/?limit=1&format=json", timeout=5)
            data  = res.json()
            score = int(data['data'][0]['value'])

            if score <= 25:   label = "극도의 공포 - 매수 기회"
            elif score <= 45: label = "공포 - 매수 고려"
            elif score <= 55: label = "중립"
            elif score <= 75: label = "탐욕 - 매도 고려"
            else:             label = "극도의 탐욕 - 매도 주의"

            return score, label

        except Exception as e2:
            print(f"alternative.me 오류: {e2}")
            return None, None

# ==========================================
# 뉴스 감성 분석
# ==========================================
def get_news_sentiment(ticker):
    try:
        url    = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=5"
        res    = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        data   = res.json()
        news   = data.get('news', [])

        if not news:
            return None, []

        # 긍정/부정 키워드
        positive = ['beat', 'surge', 'gain', 'rise', 'up', 'high', 'growth',
                    'profit', 'record', 'strong', 'buy', 'upgrade', 'bullish']
        negative = ['miss', 'fall', 'drop', 'down', 'low', 'loss', 'weak',
                    'sell', 'downgrade', 'bearish', 'cut', 'risk', 'warn']

        pos_count = 0
        neg_count = 0
        titles    = []

        for n in news[:5]:
            title = n.get('title', '').lower()
            titles.append(n.get('title', ''))
            pos_count += sum(1 for w in positive if w in title)
            neg_count += sum(1 for w in negative if w in title)

        if pos_count > neg_count:
            sentiment = f"긍정 ({pos_count}건)"
        elif neg_count > pos_count:
            sentiment = f"부정 ({neg_count}건)"
        else:
            sentiment = "중립"

        return sentiment, titles[:3]

    except Exception as e:
        print(f"뉴스 감성 오류: {e}")
        return None, []


# ==========================================
# 실적 발표일
# ==========================================
def get_earnings_date(ticker):
    try:
        stock    = yf.Ticker(ticker)
        calendar = stock.calendar

        if not calendar:
            return None

        
        earn_date = calendar.get('Earnings Date')
        if not earn_date:
            return None

        earn_date = pd.Timestamp(earn_date[0]).date()
        today     = datetime.date.today()
        days_left = (earn_date - today).days

        if days_left < 0:
            return f"지난 실적: {earn_date}"
        elif days_left == 0:
            return "오늘 실적 발표!"
        elif days_left <= 7:
            return f"실적 발표 {days_left}일 후 ({earn_date}) - 주의"
        else:
            return f"실적 발표: {earn_date} ({days_left}일 후)"

    except Exception as e:
        print(f"실적 발표일 오류: {e}")
        return None
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

    
    market, is_open = get_market_status()
    realtime        = get_realtime_price(ticker)
    fg_score, fg_label       = get_fear_greed()
    sentiment, news_titles   = get_news_sentiment(ticker)
    earnings                 = get_earnings_date(ticker)

    if is_open and realtime:
        curr        = realtime
        price_label = f"*{curr:.2f}* (실시간)"
    else:
        curr        = get_value(df['Close'])
        price_label = f"*{curr:.2f}* (전일 종가)"

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
    target_price = curr * 1.05
    stop_loss    = curr * 0.97

    buy_score, buy_signals, sell_score, sell_signals = detect_signal(df)
    judgment, _, chart_title = final_judgment(buy_score, sell_score)

    buy_text  = "\n".join([f"[매수] {s}" for s in buy_signals])  or "없음"
    sell_text = "\n".join([f"[매도] {s}" for s in sell_signals]) or "없음"

    if 'Buy' in judgment:    action = "*Buy Timing* - Consider split buying"
    elif 'Sell' in judgment: action = "*Sell Timing* - Consider split selling"
    else:                    action = "*Watch* - Wait for signal confirmation"
    # 공포탐욕지수 텍스트
    if fg_score is not None:
        fg_text = f"{fg_score}점 - {fg_label}"
    else:
        fg_text = "가져오기 실패"

    # 뉴스 텍스트
    if sentiment:
        news_text = f"감성: {sentiment}\n"
        news_text += "\n".join([f"  - {t}" for t in news_titles])
    else:
        news_text = "뉴스 없음"

    # 실적 발표 텍스트
    earnings_text = earnings if earnings else "정보 없음"

    report = (
        f"*[{ticker}] {label} 분석 리포트*\n"
        f"기준: {now_str} | 조회: {kt_str}\n"
        f"{market}\n"
        f"--------------------\n"
        f"현재가: {price_label}\n"
        f"목표가: {target_price:.2f} (+5%) | 손절가: {stop_loss:.2f} (-3%)\n"
        f"거래량: {vol:,.0f}\n"
        f"RSI: {rsi:.1f} | MACD: {macd:.3f} | Stoch K: {sk:.1f}\n"
        f"MA5: {ma5:.2f} | MA20: {ma20:.2f}\n"
        f"BB상단: {upper:.2f} | BB하단: {lower:.2f}\n\n"
        f"--------------------\n"
        f"*시장 심리*\n"
        f"공포탐욕지수: {fg_text}\n"
        f"실적 발표: {earnings_text}\n\n"
        f"*뉴스 감성*\n"
        f"{news_text}\n\n"
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

    # ✅ 몬테카를로 명령어 추가
    if len(parts) >= 2 and parts[1] in ['MC', 'MONTE', '몬테']:
        await update.message.reply_text(
            f"[분석 중] {ticker} 몬테카를로 시뮬레이션 중... 잠시만 기다려주세요."
        )
        result = montecarlo(ticker)
        if result is None:
            await update.message.reply_text(
                f"[오류] {ticker} 데이터를 가져오지 못했습니다."
            )
        else:
            await update.message.reply_text(result, parse_mode='Markdown')
        return

    if len(parts) >= 2:
        if parts[1] in ['단타', '5M', '5분']:    mode = '단타'
        elif parts[1] in ['스윙', '1H', '1시간']: mode = '스윙'

    await update.message.reply_text(
        f"[분석 중] {ticker} [{MODE_CONFIG[mode]['label']}] 잠시만 기다려주세요."
    )

    report, chart_buf = analyze(ticker, mode)

    if report is None:
        await update.message.reply_text(
            f"[오류] {ticker} 데이터를 가져오지 못했습니다.\n"
            f"입력: AAPL / AAPL 단타 / AAPL 스윙 / AAPL mc"
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
# ==========================================
# 몬테카를로 시뮬레이션
# ==========================================
def montecarlo(ticker, simulations=1000):
    try:
        df = yf.download(ticker, period='1y', interval='1d', progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        if df.empty or len(df) < 30:
            return None

        closes = df['Close'].values.flatten()
        results = {7: [], 30: [], 90: []}

        for hold_days in [7, 30, 90]:
            for _ in range(simulations):
                max_idx  = len(closes) - hold_days - 1
                if max_idx <= 0:
                    continue
                buy_idx  = random.randint(0, max_idx)
                sell_idx = buy_idx + hold_days

                buy_price  = float(closes[buy_idx])
                sell_price = float(closes[sell_idx])

                if buy_price <= 0:
                    continue

                profit = (sell_price - buy_price) / buy_price * 100
                results[hold_days].append(profit)

        report_lines = [f"*[{ticker}] Monte Carlo Simulation*",
                        f"Simulations: {simulations} times\n"]

        best_period = None
        best_winrate = 0

        for hold_days, res in results.items():
            if not res:
                continue

            arr      = np.array(res)
            win_rate = float((arr > 0).mean() * 100)
            avg_ret  = float(arr.mean())
            max_p    = float(arr.max())
            max_l    = float(arr.min())

            if win_rate > best_winrate:
                best_winrate = win_rate
                best_period  = hold_days

            # 적합도 판정
            if win_rate >= 65:   grade = "Excellent"
            elif win_rate >= 55: grade = "Good"
            elif win_rate >= 45: grade = "Neutral"
            else:                grade = "Caution"

            report_lines.append(
                f"--- Hold {hold_days} days ---\n"
                f"Win Rate: {win_rate:.1f}% | Grade: {grade}\n"
                f"Avg Return: {avg_ret:+.1f}%\n"
                f"Max Profit: {max_p:+.1f}% | Max Loss: {max_l:+.1f}%"
            )

        if best_period:
            report_lines.append(
                f"\nBest Period: {best_period} days "
                f"(Win Rate: {best_winrate:.1f}%)"
            )

        report_lines.append(
            "\n*Caution: Based on past data."
            "\nDoes not guarantee future returns.*"
        )

        return "\n".join(report_lines)

    except Exception as e:
        print(f"몬테카를로 오류: {e}")
        return None
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
