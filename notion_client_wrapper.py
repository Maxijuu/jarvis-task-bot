# notion_client_wrapper.py

import datetime
import dateparser
from notion_client import Client
import os
import logging

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")


logger = logging.getLogger(__name__)
notion = Client(auth=NOTION_TOKEN)

def get_next_weekday(date_str: str, relative_base: datetime.datetime) -> datetime.datetime:
    """
    Versucht, aus einem String wie 'next monday' den nächsten entsprechenden Wochentag zu ermitteln.
    Gibt ein datetime-Objekt zurück oder None, wenn keine passende Angabe gefunden wird.
    """
    # Mappe die Wochentage auf Zahlen (Montag=0, ..., Sonntag=6)
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }
    
    words = date_str.lower().split()
    if "next" in words:
        for word in words:
            if word in days:
                current_weekday = relative_base.weekday()
                target_weekday = days[word]
                # Berechne, wie viele Tage bis zum nächsten Auftreten des Zielwochentags vergehen
                days_ahead = (target_weekday - current_weekday + 7) % 7
                # Wenn heute der gleiche Wochentag ist, setze auf 7 (nächste Woche)
                if days_ahead == 0:
                    days_ahead = 7
                return relative_base + datetime.timedelta(days=days_ahead)
    return None


def parse_due_date(date_str: str) -> str:
    import datetime
    import dateparser
    import pytz

    tz = pytz.timezone("Europe/Berlin")
    now = datetime.datetime.now(tz)
    settings = {
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": now,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "TIMEZONE": "Europe/Berlin",
        "PARSERS": ["relative-time", "absolute-time"],
        "STRICT_PARSING": False,
    }
    # Versuch zuerst, den Datumstext mit dateparser zu parsen:
    parsed_date = dateparser.parse(date_str, settings=settings)
    if not parsed_date:
        # Fallback: versuche "next <weekday>" manuell zu berechnen
        fallback_date = get_next_weekday(date_str, now)
        if fallback_date:
            parsed_date = fallback_date
    if parsed_date:
        print (str(parsed_date) + " 1")
        return parsed_date.strftime("%Y-%m-%d")
    else:
        return None





def get_tasks_with_filter(filter_dict: dict) -> dict:
    """
    Baut einen Notion-Filter basierend auf den extrahierten Kriterien auf und fragt die Datenbank ab.
    """
    import datetime
    import dateparser

    # Falls due_date vorhanden, versuche es in ein ISO-Format (YYYY-MM-DD) umzuwandeln
    if "due_date" in filter_dict:
        iso_date = parse_due_date(filter_dict["due_date"])
        if iso_date:
            filter_dict["due_date"] = iso_date
        else:
            # Wenn das Parsen fehlschlägt, entferne den due_date-Filter
            del filter_dict["due_date"]

    filters_list = []
    if "due_date" in filter_dict:
        filters_list.append({
            "property": "Datum",
            "date": {"equals": filter_dict["due_date"]}
        })
    if "group" in filter_dict:
        filters_list.append({
            "property": "Gruppe",
            "select": {"equals": filter_dict["group"]}
        })
    if "priority" in filter_dict:
        filters_list.append({
            "property": "Priorität",
            "select": {"equals": filter_dict["priority"]}
        })
    
    notion_filter = {"and": filters_list} if filters_list else {}
    
    try:
        if notion_filter:
            result = notion.databases.query(database_id=DATABASE_ID, filter=notion_filter)
        else:
            result = notion.databases.query(database_id=DATABASE_ID)
        return result
    except Exception as e:
        logger.error("Fehler beim Abfragen der Aufgaben: " + str(e))
        return {}



def create_task_in_notion(data: dict) -> bool:
    """
    Erstellt eine Aufgabe in Notion basierend auf den übergebenen Daten.
    """
    try:
        properties = {
            "Name": {"title": [{"text": {"content": data.get("task_name", "Unbenannte Aufgabe")}}]}
        }
        # Dynamische Gruppenzuweisung:
        group_input = data.get("group", "").strip().lower()
        if "maxi" in group_input:
            group_mapped = "Maxi"
        elif "familie" in group_input:
            group_mapped = "Familie"
        elif "nina" in group_input:
            group_mapped = "Freundin"
        elif "fsv" in group_input:
            group_mapped = "FSV"
        else:
            group_mapped = "Freunde"
        properties["Gruppe"] = {"select": {"name": group_mapped}}
        
        if "priority" in data and data["priority"].strip():
            properties["Priorität"] = {"select": {"name": data["priority"]}}
        if "due_date" in data and data["due_date"].strip():
            parsed_date = dateparser.parse(
                data["due_date"],
                languages=["en"],
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": datetime.datetime.now(),
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "TIMEZONE": "Europe/Berlin"
                }
            )
            if parsed_date:
                iso_date = parsed_date.isoformat()
                properties["Datum"] = {"date": {"start": iso_date}}
            else:
                logger.error("Konnte das Datum nicht parsen: " + data["due_date"])
        
        notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
        return True
    except Exception as e:
        logger.error(f"Fehler bei Notion-Erstellung: {e}")
        return False
