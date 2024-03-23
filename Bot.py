import os
import time
import logging
import telebot
from telebot import types
from Utils import log
from GitHubSearch import get_inline_data, get_message_url_and_buttons_for
from flask import Flask, redirect, request, abort
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APP_ADDRESS = os.environ.get("APP_ADDRESS")
WEBHOOK_PORT = os.environ.get("PORT")
WEBHOOK_PATH = f"/{BOT_TOKEN}/"
WEBHOOK_URL = f"https://{APP_ADDRESS}:{WEBHOOK_PORT}" + WEBHOOK_PATH

bot = telebot.TeleBot(BOT_TOKEN,threaded=False)
BOT_USERNAME = bot.get_me().username
telebot.logger.setLevel(logging.INFO)

bot.remove_webhook()
time.sleep(0.1)
bot.set_webhook(url=WEBHOOK_URL)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def testing():
    return redirect(f"https://t.me/{BOT_USERNAME}", code=302)


# Process webhook calls
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)


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