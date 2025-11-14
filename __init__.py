"""
Secret Santa Organizer Package
"""

__version__ = "1.0.0"
__author__ = "Andrea"

from .participants_manager import ParticipantsManager
from .extractions_manager import ExtractionsManager
from .email_manager import EmailManager

__all__ = [
    "ParticipantsManager",
    "ExtractionsManager", 
    "EmailManager"
]