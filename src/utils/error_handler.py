import logging

logger = logging.getLogger("ErrorHandler")

class ErrorHandler:
    @staticmethod
    def handle_error(error, context=""):
        """Logga gli errori con contesto aggiuntivo."""
        if logger:
            logger.error(f"{context} - {error}")
        else:
            print(f"Errore non loggato: {context} - {error}")
