
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from hyperliquid.info import Info
from hyperliquid.utils import constants

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WALLET = os.environ["HYPERLIQUID_ADDRESS"].strip()
ALLOWED_ID = int(os.environ["TELEGRAM_USER_ID"])

info = Info(constants.MAINNET_API_URL, skip_ws=True)


def authorized(update):
    return (
        update.effective_user is not None
        and update.effective_user.id == ALLOWED_ID
        and update.effective_chat is not None
        and update.effective_chat.type == "private"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return
    await update.message.reply_text(
        "ANT Monitor online.\n"
        "Commands: /status, /orders\n"
        "Read-only mode: trading disabled."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return
    try:
        state = info.user_state(WALLET)
        positions = state.get("assetPositions", [])
        if not positions:
            message = "No standard perp positions found."
        else:
            lines = []
            for item in positions:
                p = item["position"]
                lines.append(
                    f"{p['coin']}: size {p['szi']}, "
                    f"entry {p['entryPx']}, "
                    f"liq {p.get('liquidationPx', 'N/A')}"
                )
            message = "\n".join(lines)
        await update.message.reply_text(message[:4000])
    except Exception:
        logging.exception("Status request failed")
        await update.message.reply_text(
            "Could not retrieve positions. Check server logs."
        )


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return
    try:
        data = info.frontend_open_orders(WALLET)
        if not data:
            message = "No standard perp open orders found."
        else:
            lines = [
                f"{o.get('coin')}: {o.get('side')} "
                f"{o.get('sz')} @ {o.get('limitPx')}"
                for o in data
            ]
            message = "\n".join(lines)
        await update.message.reply_text(message[:4000])
    except Exception:
        logging.exception("Orders request failed")
        await update.message.reply_text(
            "Could not retrieve orders. Check server logs."
        )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("orders", orders))
    app.run_polling()


if __name__ == "__main__":
    main()
  
