# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from telegram_handler import start, handle_message, send_daily_tasks
import logging
import datetime

logging.basicConfig(level=logging.ERROR)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handler für /start und eingehende Textnachrichten
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Definiere die Chat-ID, an die die tägliche Nachricht gesendet werden soll.
    # Ersetze '123456789' durch deine tatsächliche Telegram-Chat-ID.
    chat_id = 7900504720
    
    # Plane den täglichen Job: Sende jeden Morgen um 08:00 Uhr die Aufgaben.
    run_time = datetime.time(hour=7, minute=0, second=0)
    application.job_queue.run_daily(send_daily_tasks, run_time, data={"chat_id": chat_id})
    

    
    application.run_polling()

if __name__ == '__main__':
    main()
