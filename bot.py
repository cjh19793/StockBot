"""텔레그램 봇 핸들러 및 실행."""
import asyncio
import logging
import re

from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from analysis import analyze
from config import MC_CONFIG, MODE_ALIASES, MODE_CONFIG, require_token
from montecarlo import montecarlo

log = logging.getLogger(__name__)

_TICKER_RE = re.compile(r"^[A-Z0-9^][A-Z0-9.^-]{0,9}$")
_MC_KEYWORDS = {"MC", "MONTE", "몬테"}

USAGE = (
    "사용법:\n"
    "  AAPL          기본(일봉) 분석\n"
    "  AAPL 단타     5분봉 분석\n"
    "  AAPL 스윙     1시간봉 분석\n"
    "  AAPL mc       몬테카를로 (기본)\n"
    "  AAPL mc 스윙  몬테카를로 (단타/스윙/장기 선택)"
)


def _resolve_mode(token: str, allowed) -> str | None:
    canon = MODE_ALIASES.get(token)
    return canon if canon in allowed else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(USAGE)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    parts = update.message.text.strip().upper().split()
    if not parts:
        return

    ticker = parts[0]
    if not _TICKER_RE.match(ticker):
        await update.message.reply_text(f"티커를 인식할 수 없습니다.\n\n{USAGE}")
        return

    # 몬테카를로: "TICKER mc [모드]"
    if len(parts) >= 2 and parts[1] in _MC_KEYWORDS:
        mc_mode = "기본"
        if len(parts) >= 3:
            mc_mode = _resolve_mode(parts[2], MC_CONFIG) or "기본"
        await update.message.reply_text(
            f"[분석 중] {ticker} Monte Carlo ({mc_mode}) 잠시만 기다려주세요."
        )
        result = await asyncio.to_thread(montecarlo, ticker, mc_mode)
        if result is None:
            await update.message.reply_text(f"[오류] {ticker} 데이터를 가져오지 못했습니다.")
        else:
            await update.message.reply_text(result, parse_mode="Markdown")
        return

    # 일반 분석: "TICKER [모드]"
    mode = "기본"
    if len(parts) >= 2:
        mode = _resolve_mode(parts[1], MODE_CONFIG) or "기본"

    await update.message.reply_text(
        f"[분석 중] {ticker} [{MODE_CONFIG[mode]['label']}] 잠시만 기다려주세요."
    )
    report, chart_buf = await asyncio.to_thread(analyze, ticker, mode)

    if report is None:
        await update.message.reply_text(
            f"[오류] {ticker} 데이터를 가져오지 못했습니다.\n\n{USAGE}"
        )
        return

    await update.message.reply_text(report, parse_mode="Markdown")
    await update.message.reply_photo(
        photo=chart_buf,
        read_timeout=60, write_timeout=60, connect_timeout=60, pool_timeout=60,
        caption=f"{ticker} {MODE_CONFIG[mode]['label']} 차트",
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("처리 중 오류", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "[오류] 요청 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
        except Exception:
            pass


def main():
    token = require_token()
    log.info("텔레그램 봇 시작")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    app.run_polling()
