import requests
import os
import logging
import redis

from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackContext)


class HKBU_ChatGPT():
    """
    chatgpt client
    code from ChatGPT_HKBU.py
    """
    def __init__(self):
        pass

    def submit(self,message):
        conversation = [{"role": "user", "content": message}]
        basic_url = os.environ['GPT_BASICURL']
        modelname = os.environ['GPT_MODELNAME']
        version = os.environ['GPT_APIVERSION']
        accesstoken = os.environ['GPT_ACCESS_TOKEN']
        url = (basic_url) + "/deployments/" + (modelname) + "/chat/completions/?api-version=" + (version)
        headers = {'Content-Type': 'application/json', 'api-key': accesstoken}
        payload = {'messages': conversation }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return 'Error:', response


def init_redis():
    return redis.from_url(os.environ['REDIS_URL'])


def main():
    # Load your token and create an Updater for your Bot
    updater = Updater(token=(os.environ['TELEGRRAM_ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # register a dispatcher to handle message: here we register an echo dispatcher
    # echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    # dispatcher.add_handler(echo_handler)

    # dispatcher for chatgpt
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), equiped_chatgpt)
    dispatcher.add_handler(chatgpt_handler)

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("hello", hello_command))
    dispatcher.add_handler(CommandHandler("history", history_command))
    dispatcher.add_handler(CommandHandler('mr', mr_command))

    # To start the bot:
    updater.start_polling()
    updater.idle()


def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)


def equiped_chatgpt(update, context):
    reply_message = chat_gpt.submit(update.message.text)
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    redis_client.lpush("history", update.message.text)
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Helping you helping you.')


def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try:
        logging.info(context.args[0])
        msg = context.args[0]   # /add keyword <-- this should store the keyword
        redis_client.incr(msg)
        update.message.reply_text('You have said ' + msg +  ' for ' + redis_client.get(msg).decode('UTF-8') + ' times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')


def hello_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /hello is issued."""
    msg = context.args[0]
    update.message.reply_text('Good day, {}!'.format(msg))


def history_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /hello is issued."""
    # msg = context.args[0]
    history = redis_client.lrange("history", 0, -1)
    # for h in history:
    #     print(h)
    update.message.reply_text('Message num: {}\nLast message: {}'.format(len(history), history[0].decode()))


def mr_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /hello is issued."""
    msg = context.args[0]
    reply_message = chat_gpt.submit("write a short movie review of "+msg)
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)


if __name__ == '__main__':
    redis_client = init_redis()
    chat_gpt = HKBU_ChatGPT()
    main()
