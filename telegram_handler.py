# telegram_handler.py

from telegram import Update
from telegram.ext import ContextTypes
from openai_client import determine_intent, process_input_with_openai, determine_filter
from notion_client_wrapper import create_task_in_notion, get_tasks_with_filter
import logging
import datetime

logger = logging.getLogger(__name__)

async def flexible_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Führt eine flexible Abfrage durch: Extrahiert Filterkriterien aus der Anfrage, 
    fragt Notion ab und gibt die gefundenen Aufgaben zurück.
    """
    query_text = update.message.text
    filter_dict = determine_filter(query_text)
    logger.info("Extrahierte Filter: " + str(filter_dict))
    
    result = get_tasks_with_filter(filter_dict)
    tasks = result.get("results", [])
    
    if tasks:
        message = "Gefundene Aufgaben:\n"
        for task in tasks:
            title_items = task["properties"]["Name"]["title"]
            if title_items:
                task_name = "".join([item["text"]["content"] for item in title_items])
            else:
                task_name = "Unbenannte Aufgabe"
            message += f"- {task_name}\n"
    else:
        message = "Keine Aufgaben gefunden, die zu deiner Anfrage passen."
    
    await update.message.reply_text(message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Bestimmt die Intention der eingehenden Nachricht und leitet sie weiter.
    """
    user_message = update.message.text
    intent = determine_intent(user_message)
    if intent == "query_tasks":
        await flexible_query(update, context)
    elif intent == "create_task":
        await update.message.reply_text("Ich verarbeite deine Aufgabe...")
        task_data = process_input_with_openai(user_message)
        if not task_data:
            await update.message.reply_text("Fehler: Konnte die Aufgabe nicht extrahieren.")
            return
        success = create_task_in_notion(task_data)
        if success:
            await update.message.reply_text(f"Jarvis hat die Task '{task_data['task_name']}' erstellt!")
        else:
            await update.message.reply_text("Fehler beim Speichern in Notion.")
    else:
        await update.message.reply_text("Ich konnte deine Anfrage nicht zuordnen. Bitte formuliere sie anders.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sendet eine Begrüßungsnachricht, wenn der Bot gestartet wird.
    """
    await update.message.reply_text(
        "Willkommen! Du kannst Aufgaben erstellen oder nach Aufgaben filtern.\n"
        "Schreibe z.B. 'Erstelle eine Aufgabe ...' oder 'Welche Aufgaben habe ich morgen?'."
    )

async def send_daily_tasks(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sendet jeden Morgen eine Nachricht mit den Aufgaben, die an diesem Tag zu erledigen sind.
    Die Chat-ID wird über den Job-Context bereitgestellt.
    """
    # Heutiges Datum im Format YYYY-MM-DD
    logger.info("send_daily_tasks wurde gestartet!")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filter_dict = {"due_date": today}
    result = get_tasks_with_filter(filter_dict)
    tasks = result.get("results", [])
    
    if tasks:
        message = "Guten Morgen! Hier sind deine Aufgaben für heute:\n"
        for task in tasks:
            title_items = task["properties"]["Name"]["title"]
            if title_items:
                task_name = "".join([item["text"]["content"] for item in title_items])
            else:
                task_name = "Unbenannte Aufgabe"
            message += f"- {task_name}\n"
    else:
        message = "Guten Morgen! Für heute stehen keine Aufgaben an."
    
    # Chat-ID aus dem Job-Context (muss in main.py gesetzt werden)
    chat_id = context.job.data.get("chat_id")
    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logger.error("Fehler beim Senden der täglichen Nachricht: " + str(e))

