# src/tools/python_repl_tool.py

import logging
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
import io
import contextlib

logger = logging.getLogger("PythonREPLTool")

def execute_code(code: str) -> str:
    """
    Esegue il codice Python fornito in un ambiente sicuro e restituisce l'output.

    Args:
        code (str): Codice Python da eseguire.

    Returns:
        str: Output dell'esecuzione del codice.
    """
    try:
        # Compila il codice in modalità restrittiva
        byte_code = compile_restricted(code, '<string>', 'exec')
        
        # Prepara gli ambienti globali e locali con built-ins limitati
        restricted_globals = {
            '__builtins__': safe_builtins,
            '_print_': print,  # Consenti solo l'uso di print
            '_getattr_': getattr,
            '_setattr_': setattr,
            '_getitem_': lambda obj, key: obj[key],
            '_getiter_': iter,
            '_write_': lambda obj: obj,  # Consenti la scrittura
        }
        restricted_locals = {}
        
        # Cattura l'output standard
        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            exec(byte_code, restricted_globals, restricted_locals)
        output = captured_output.getvalue()
        logger.debug(f"Codice eseguito con successo. Output: {output}")
        return output
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del codice: {e}")
        return f"Errore nell'esecuzione del codice: {e}"
