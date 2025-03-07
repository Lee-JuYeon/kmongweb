import os
import telegram_manager
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드

telebot_token = os.getenv('telebot_token')
print("텔레그램 봇 토큰:", telebot_token)

API_TOKEN = telebot_token
bot = telegram_manager.TeleBot(API_TOKEN)

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
""")

# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    print("Chat ID:", message.chat.id)  # chat_id 출력
    bot.reply_to(message, message.text)

# 봇 실행
bot.infinity_polling()

"""
Chat ID 얻는법
1. BotFather으로부터 'HTTP API' 토큰을 받는다.
2. telebot_chat_id_checker.py를 실행한다.
3. 봇에 아무런 메세지를 보낸다.
4. 터미널에 Chat ID를 확인한다.
"""