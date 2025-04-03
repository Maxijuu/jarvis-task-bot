# openai_client.py

import json
from openai import OpenAI
from config import OPENAI_API_KEY
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

def determine_intent(user_message: str) -> str:
    """
    Nutzt GPT, um die Intention der Anfrage zu bestimmen.
    Erwartete Rückgaben: 'create_task' oder 'query_tasks'
    """
    prompt = (
        "Klassifiziere die folgende Anfrage in eine von zwei Kategorien: 'create_task' "
        "für das Erstellen einer Aufgabe, oder 'query_tasks' für eine Abfrage der Aufgaben. "
        "Antworte bitte nur mit 'create_task' oder 'query_tasks'.\n\n"
        f"Anfrage: {user_message}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=10,
            temperature=0
        )
        intent = response.choices[0].message.content.strip().lower()
        return intent
    except Exception as e:
        logger.error(f"Fehler beim Bestimmen der Intention: {e}")
        return None

def determine_filter(query: str) -> dict:
    """
    Extrahiere aus der Anfrage Filterkriterien (due_date, group, priority) mithilfe von GPT.
    Gibt ein JSON-Objekt zurück, z.B. {"due_date": "2025-02-28", "group": "Familie"}
    """
    prompt = (
        "Extrahiere aus der folgenden Anfrage Filterkriterien, um Aufgaben in Notion abzufragen. "
        "Mögliche Filter sind:\n"
        "- due_date (im Format YYYY-MM-DD)\n"
        "- group (z. B. 'Familie', 'Maxi', 'Freundin', 'Freunde')\n"
        "- priority (z. B. 'hoch', 'mittel', 'niedrig')\n\n"
        "Gib das Ergebnis als JSON-Objekt zurück. "
        "Wenn kein Filter angegeben ist, gib ein leeres Objekt {} zurück.\n\n"
        f"Anfrage: {query}\n\n"
        "Beispiel: {{\"due_date\": \"2025-02-28\", \"group\": \"Familie\"}}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=100,
            temperature=0
        )
        filter_json = response.choices[0].message.content.strip()
        filter_dict = json.loads(filter_json)
        print (filter_dict)
        return filter_dict
    except Exception as e:
        logger.error("Fehler beim Bestimmen der Filter: " + str(e))
        return {}

def process_input_with_openai(user_message: str) -> dict:
    """
    Sendet den Nutzertext an GPT und erwartet ein JSON-Objekt zur Aufgabenerstellung.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bist ein Task-Manager-Assistent. Bitte antworte IMMER in folgendem JSON-Format:\n\n"
                        "{\n"
                        "  \"task_name\": \"...\",\n"
                        "  \"due_date\": \"...\",  // Gib das Datum so zurück, dass der Dateparser es versteht (auf Englisch)\n"
                        "  \"priority\": \"...\", // kategorisiere zwischen 'Wichtig', 'Mittel', 'Niedrig' – falls Eingabe fehlt, setze auf 'Mittel'\n"
                        "  \"group\": \"...\" // falls Eingabe fehlt, setze auf 'Maxi'\n"
                        "}\n\n"
                    )
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.5
        )
        result_text = response.choices[0].message.content.strip()
        print(result_text)
        task_data = json.loads(result_text)
        return task_data
    except json.JSONDecodeError:
        logger.error("Fehler: Ungültiges JSON von OpenAI.")
        return None
    except Exception as e:
        logger.error(f"OpenAI-Fehler: {e}")
        return None
    
