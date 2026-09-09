"""분석 차트 렌더링 (pyplot 전역 상태 없이 Figure 직접 사용)."""
import io

import matplotlib
import numpy as np
from matplotlib.figure import Figure

from indicators import get_value

matplotlib.rcParams["axes.unicode_minus"] = False


def build_chart(df, *, ticker, label, now_str, market, chart_title,
                target_price, stop_loss, buy_score, sell_score, bar_width) -> io.BytesIO:
    fig = Figure(figsize=(14, 18))
    ax1, ax2, ax3, ax4, ax5 = fig.subplots(5, 1, sharex=True)
    idx = df.index

    # --- 가격 + 이동평균 + 볼린저 ---
    ax1.plot(idx, df["Close"], color="black", label="Price", linewidth=1.5, zorder=3)
    ax1.plot(idx, df["MA5"], color="orange", label="MA5", linewidth=1.0, linestyle="--")
    ax1.plot(idx, df["MA20"], color="blue", label="MA20", linewidth=1.0, linestyle="--")
    ax1.plot(idx, df["Upper"], color="red", label="BB Upper", alpha=0.4, linewidth=1)
    ax1.plot(idx, df["Lower"], color="blue", label="BB Lower", alpha=0.4, linewidth=1)
    ax1.fill_between(idx, df["Lower"], df["Upper"], color="gray", alpha=0.1)
    ax1.axhline(target_price, color="green", linestyle="--", alpha=0.6, linewidth=1.2,
                label=f"Target {target_price:.2f}")
    ax1.axhline(stop_loss, color="red", linestyle="--", alpha=0.6, linewidth=1.2,
                label=f"Stop {stop_loss:.2f}")

    hi_idx, hi_val = df["High"].idxmax(), float(df["High"].max())
    lo_idx, lo_val = df["Low"].idxmin(), float(df["Low"].min())
    for m_idx, val, color, fc, offset, txt in [
        (hi_idx, hi_val, "red", "#ffebee", 14, f"High {hi_val:.2f}"),
        (lo_idx, lo_val, "blue", "#e3f2fd", -20, f"Low {lo_val:.2f}"),
    ]:
        ax1.scatter(m_idx, val, color=color, marker="*", s=250, zorder=5)
        ax1.annotate(txt, xy=(m_idx, val), xytext=(0, offset), textcoords="offset points",
                     ha="center", fontsize=9, fontweight="bold", color=color,
                     bbox=dict(boxstyle="round,pad=0.3", facecolor=fc, edgecolor=color, alpha=0.9))

    if buy_score > sell_score and buy_score > 0:
        ax1.set_facecolor("#e8f5e9")
    elif sell_score > buy_score:
        ax1.set_facecolor("#ffebee")
    ax1.set_title(f"{ticker} [{label}] - {chart_title} | {now_str} | {market}",
                  fontsize=13, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=7, ncol=3)
    ax1.grid(True, alpha=0.2)

    # --- 거래량 ---
    close = df["Close"].to_numpy().ravel()
    open_ = df["Open"].to_numpy().ravel()
    ax2.bar(idx, df["Volume"].to_numpy().ravel(),
            color=np.where(close >= open_, "red", "blue"), alpha=0.7, width=bar_width)
    ax2.plot(idx, df["Volume"].rolling(20).mean(), color="orange", linewidth=1.2,
             linestyle="--", label="Volume 20MA")
    ax2.set_ylabel("Volume")
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(True, alpha=0.2)

    # --- RSI ---
    rsi = get_value(df["RSI"])
    ax3.plot(idx, df["RSI"], color="purple", label="RSI (14)", linewidth=1.5)
    ax3.axhline(70, color="red", linestyle="--", alpha=0.5, label="Overbought(70)")
    ax3.axhline(50, color="gray", linestyle=":", alpha=0.4)
    ax3.axhline(30, color="blue", linestyle="--", alpha=0.5, label="Oversold(30)")
    ax3.fill_between(idx, 70, 100, where=(df["RSI"] >= 70), color="red", alpha=0.15)
    ax3.fill_between(idx, 0, 30, where=(df["RSI"] <= 30), color="blue", alpha=0.15)
    ax3.scatter(idx[-1], rsi, color="purple", zorder=5, s=80)
    ax3.annotate(f"  {rsi:.1f}", xy=(idx[-1], rsi), color="purple", fontweight="bold", fontsize=10)
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("RSI")
    ax3.legend(loc="upper left", fontsize=8)
    ax3.grid(True, alpha=0.2)

    # --- MACD ---
    ax4.plot(idx, df["MACD"], color="blue", label="MACD", linewidth=1.2)
    ax4.plot(idx, df["MACD_signal"], color="orange", label="Signal", linewidth=1.2)
    hist = df["MACD_hist"].to_numpy().ravel()
    ax4.bar(idx, hist, color=np.where(hist >= 0, "red", "blue"), alpha=0.4,
            width=bar_width, label="Histogram")
    ax4.axhline(0, color="gray", linestyle="--", alpha=0.4)
    ax4.set_ylabel("MACD")
    ax4.legend(loc="upper left", fontsize=8)
    ax4.grid(True, alpha=0.2)

    # --- 스토캐스틱 ---
    ax5.plot(idx, df["Stoch_K"], color="green", label="%K", linewidth=1.2)
    ax5.plot(idx, df["Stoch_D"], color="red", label="%D", linewidth=1.2)
    ax5.axhline(80, color="red", linestyle="--", alpha=0.5, label="Overbought(80)")
    ax5.axhline(20, color="blue", linestyle="--", alpha=0.5, label="Oversold(20)")
    ax5.fill_between(idx, 80, 100, where=(df["Stoch_K"] >= 80), color="red", alpha=0.15)
    ax5.fill_between(idx, 0, 20, where=(df["Stoch_K"] <= 20), color="blue", alpha=0.15)
    ax5.set_ylim(0, 100)
    ax5.set_ylabel("Stochastic")
    ax5.legend(loc="upper left", fontsize=8)
    ax5.grid(True, alpha=0.2)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    return buf
