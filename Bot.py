import os
import logging
from telebot import TeleBot
from telebot import telebot, types
from Utils import log
from GitHubSearch import get_inline_data, get_message_url_and_buttons_for
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN,threaded= False)
BOT_USERNAME = bot.get_me().username

telebot.logger.setLevel(logging.INFO)


# send welcome message
def send_welcome(message):
    buttons = types.InlineKeyboardMarkup()
    btn_here = types.InlineKeyboardButton(
        text="Go inline here", switch_inline_query_current_chat=""
    )
    btn_there = types.InlineKeyboardButton(
        text="Go inline in a chat",
        switch_inline_query_chosen_chat=types.SwitchInlineQueryChosenChat(
            query="",
            allow_bot_chats=True,
            allow_channel_chats=True,
            allow_group_chats=True,
            allow_user_chats=True,
        ),
    )
    buttons.row(btn_here, btn_there)
    bot.reply_to(
        message,
        text=f"Hello {message.from_user.first_name},\nThis bot works only in inline mode.",
        reply_markup=buttons,
    )


# handle commands
@bot.message_handler(commands=["help", "start"])
def handle_commands(message):
    if message.text.endswith("help"):
        url = "https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories"
        button = types.InlineKeyboardMarkup()
        button.add(types.InlineKeyboardButton("Search Documentation",url=url))
        bot.reply_to(message=message,text="See the documentation to write better search query.",reply_markup=button)
    else:
        send_welcome(message)


# All text message handled here
@bot.message_handler(func=lambda message: True)
def received_message(message):
    # don't reply to own messages
    if message.via_bot is not None and message.via_bot.username == BOT_USERNAME:
        return
    else:
        send_welcome(message)


# handle inline queries
@bot.inline_handler(func=lambda query: len(query.query) > 0)
def query_text(inline_query):
    id = str(inline_query.id)
    query = inline_query.query
    log(f"searching for {query}")
    results = get_inline_data(query)
    if results:
        button = None
    else:
        button = types.InlineQueryResultsButton(
            "No result found!", start_parameter="help"
        )
        log("No Result Found for " + query)
    bot.answer_inline_query(id, results, button=button)


@bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
def update_message_with_latest_release(chosen):
    id = chosen.inline_message_id
    message, buttons = get_message_url_and_buttons_for(chosen.result_id)
    if message is not None and buttons is not None:
        bot.edit_message_text(
            text=message, inline_message_id=id, parse_mode="html", reply_markup=buttons
        )
    else:
        log("failed to get chosen result details. Id: "+id)


if __name__ == "__main__":
    bot.infinity_polling()
