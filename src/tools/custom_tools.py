# src/tools/custom_tools.py

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
import logging

logger = logging.getLogger("CustomTools")

# Strumento per la ricerca
tavily_tool = TavilySearchResults(max_results=5)

# Strumento per eseguire codice Python
repl = PythonREPL()

@tool
def python_repl_tool(code: str):
    """Esegue codice Python e restituisce l'output."""
    try:
        result = repl.run(code)
    except Exception as e:
        return f"Errore nell'esecuzione del codice: {repr(e)}"
    return f"Risultato dell'esecuzione:\n```\n{code}\n```\nOutput: {result}"
