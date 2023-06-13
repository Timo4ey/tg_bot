import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from tg_bot.memes import (
    get_carousels,
    get_posts,
    is_valid_group,
    save_group,
    save_user,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_user(update.effective_chat)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def agreement_buttons(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    keyboard = [
        [
            InlineKeyboardButton(
                "Get posts",
                callback_data=":".join(["posts", update.message.text]),
            ),
            InlineKeyboardButton(
                "Get carousels",
                callback_data=":".join(["carousels", update.message.text]),
            ),
        ],
        [InlineKeyboardButton("No", callback_data="0")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Do you want to get meme(s) for {update.message.text}\
                                     hour(s)?",
        reply_markup=reply_markup,
    )


async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        query = update.message.text
        match await is_valid_group(query):
            case True:
                await save_group(query)
                await update.message.reply_text("The group has been saved")
            case _:
                await update.message.reply_text(
                    "The message must contains only group name and id.\
                     Example: `group Telegram id 123456789`"
                )


async def send_memes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    query = update.callback_query
    await query.answer()

    request, hours = query.data.split(":")
    match request:
        case "posts":
            await get_posts(chat_id, context, hours=hours)
        case "carousels":
            await get_carousels(chat_id, context, hours=hours)


if __name__ == "__main__":
    load_dotenv()

    application = ApplicationBuilder().token(os.getenv("TG_TOKEN")).build()

    start_handler = CommandHandler("start", start)
    memes_handler = MessageHandler(
        filters.Regex(r"^[1-9][0-9]?$|^100$"), agreement_buttons
    )
    add_group_handler = MessageHandler(
        filters.Regex(r"(^group.\w+|id.\d+$)"), add_group
    )

    application.add_handler(start_handler)
    application.add_handler(memes_handler)
    application.add_handler(add_group_handler)
    application.add_handler(CallbackQueryHandler(send_memes))
    application.add_handler(CallbackQueryHandler(add_group))
    application.run_polling()
