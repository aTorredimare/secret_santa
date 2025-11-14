"""
Eccezioni personalizzate per il Secret Santa.
"""


class SecretSantaException(Exception):
    """Eccezione base per il Secret Santa."""
    pass


class ParticipantsLoadError(SecretSantaException):
    """Errore nel caricamento dei partecipanti."""
    pass


class ExtractionError(SecretSantaException):
    """Errore nell'estrazione degli abbinamenti."""
    pass


class EmailError(SecretSantaException):
    """Errore nell'invio delle email."""
    pass


class ValidationError(SecretSantaException):
    """Errore di validazione dei dati."""
    pass