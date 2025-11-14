"""
Modulo per la gestione dei partecipanti del Secret Santa.
"""

import json
import logging
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
import re

from exceptions import ParticipantsLoadError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class Participant:
    """Rappresenta un partecipante del Secret Santa."""
    name: str
    email: str
    last_year: str = ""
    is_already_extracted: bool = False
    
    def __post_init__(self):
        if not self.validate_email(self.email):
            raise ValidationError(f"Email non valida per {self.name}: {self.email}")

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validazione email con regex più robusta."""
        if not email or not isinstance(email, str):
            return False
        email = email.strip()
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class ParticipantsManager:
    """Classe per gestire il caricamento e validazione dei partecipanti."""
    
    @classmethod
    def load_from_file(cls, file_path: str = "participants.json") -> Dict[str, Participant]:
        """
        Carica i partecipanti da un file JSON.
        
        Returns:
            Dict[str, Participant]: Dizionario dei partecipanti
        Raises:
            ParticipantsLoadError: Se il caricamento fallisce
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            participants = {}
            for name, participant_data in data.items():
                try:
                    participant = Participant(
                        name=name,
                        email=participant_data.get('email', ''),
                        last_year=participant_data.get('last_year', '') or ""
                    )
                    participants[name] = participant
                except ValidationError as e:
                    logger.error(f"Errore validazione per {name}: {e}")
                    raise ParticipantsLoadError(f"Dati non validi per {name}") from e
            
            cls._validate_constraints(participants)
            logger.info(f"Caricati {len(participants)} partecipanti da {file_path}")
            return participants
            
        except FileNotFoundError as e:
            raise ParticipantsLoadError(f"File {file_path} non trovato") from e
        except json.JSONDecodeError as e:
            raise ParticipantsLoadError(f"Errore nel parsing JSON: {e}") from e
        except Exception as e:
            raise ParticipantsLoadError(f"Errore nel caricamento partecipanti: {e}") from e
    
    @classmethod
    def load_from_file_legacy(cls, file_path: str = "participants.json") -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Versione legacy per compatibilità con il resto del codice.
        Converte i Participant in dizionari per retrocompatibilità.
        
        Returns:
            Optional[Dict[str, Dict[str, Any]]]: Dizionario dei partecipanti o None se errore
        """
        try:
            participants = cls.load_from_file(file_path)
            # Converte da Participant a dict per compatibilità
            return {
                name: {
                    'email': p.email,
                    'last_year': p.last_year,
                    'is_already_extracted': p.is_already_extracted
                }
                for name, p in participants.items()
            }
        except ParticipantsLoadError as e:
            logger.error(str(e))
            return None
    
    @staticmethod
    def _validate_constraints(participants: Dict[str, Participant]) -> None:
        """Valida i vincoli dei partecipanti."""
        participant_names = set(participants.keys())
        
        for participant in participants.values():
            if participant.last_year and participant.last_year not in participant_names:
                logger.warning(
                    f"Il last_year '{participant.last_year}' per {participant.name} "
                    f"non è un partecipante attuale"
                )
        
        # Verifica email duplicate
        emails = [p.email.lower() for p in participants.values()]
        duplicates = set([email for email in emails if emails.count(email) > 1])
        if duplicates:
            raise ValidationError(f"Email duplicate trovate: {duplicates}")
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validazione base dell'email (metodo legacy)."""
        return Participant.validate_email(email)