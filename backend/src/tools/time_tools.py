# src/tools/time_tools.py

import datetime

def get_structured_time():
    """
    Restituisce l'orario locale in formato dizionario.
    
    Returns:
        dict: Ora corrente con ore, minuti e secondi.
    """
    now = datetime.datetime.now()
    return {"hour": now.hour, "minute": now.minute, "second": now.second}
