"""
Secret Santa Organizer Package
"""

__version__ = "2.0.0"
__author__ = "Andrea"

from .participants_manager import ParticipantsManager
from .extractions_manager import ExtractionsManager
from .email_manager import EmailManager
from .database_manager import DatabaseManager

__all__ = [
    "ParticipantsManager",
    "ExtractionsManager", 
    "EmailManager",
    "DatabaseManager"
]