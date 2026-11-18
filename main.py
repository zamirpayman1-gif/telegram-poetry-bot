import os
import sqlite3
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_IDS = os.getenv("ADMIN_IDS", "")

admins = [int(x.strip()) for x in ADMIN_IDS.split(",") if x.strip()]

# ذخیره متن‌ها
db = sqlite3.connect("poems.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS poems (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL
)
""")
db.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 🤖\n"
        "ربات نمایش شعر و متن آماده است.\n"
        "برای ساخت پست از دستور /post استفاده کن."
    )


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in admins:
        await update.message.reply_text("⛔ اجازه استفاده از این دستور را نداری.")
        return

    text = " ".join(context.args)

    if "|" not in text:
        await update.message.reply_text(
            "فرمت درست:\n\n"
            "/post عنوان پست | متن مخفی\n\n"
            "مثال:\n"
            "/post یک شعر زیبا | زندگی زیباست، اگر با امید نگاهش کنیم."
        )
        return

    title, content = text.split("|", 1)
    title = title.strip()
    content = content.strip()

    if not title or not content:
        await update.message.reply_text("عنوان و متن نباید خالی باشند.")
        return

    import uuid
    poem_id = uuid.uuid4().hex[:12]

    db.execute(
        "INSERT INTO poems (id, content) VALUES (?, ?)",
        (poem_id, content)
    )
    db.commit()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 نمایش متن", callback_data=poem_id)]
    ])

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=title,
            reply_markup=keyboard
        )
        await update.message.reply_text("✅ پست با موفقیت در کانال نشر شد.")
    except Exception as e:
        logging.exception(e)
        await update.message.reply_text(
            "❌ پست نشر نشد. شناسه کانال و دسترسی ربات را بررسی کن."
        )


async def show_poem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    result = db.execute(
        "SELECT content FROM poems WHERE id = ?",
        (query.data,)
    ).fetchone()

    if result:
        content = result[0]

        # نمایش متن در پنجره کوچک تلگرام
        await query.answer(text=content, show_alert=True)
    else:
        await query.answer(
            "متن پیدا نشد؛ ممکن است ربات دوباره راه‌اندازی شده باشد.",
            show_alert=True
        )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده است!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CallbackQueryHandler(show_poem))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
