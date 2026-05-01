def main():
    print("텔레그램 봇 시작!")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    app.add_error_handler(error_handler)

    # ✅ 백그라운드 급등 탐지
    async def start_background(app):
        print("급등주 스캔 시작")
        asyncio.create_task(auto_surge_loop(app))

    app.post_init = start_background

    app.run_polling()


if __name__ == "__main__":
    main()
