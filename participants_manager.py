"""
Modulo per la gestione dei partecipanti del Secret Santa.
"""

import json
import logging
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
import re
from datetime import datetime

from exceptions import ParticipantsLoadError, ValidationError
from database_manager import DatabaseManager, ParticipantRecord

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
    
    def __init__(self, db_path: str = "secret_santa.db"):
        """Inizializza il manager con database opzionale."""
        self.db_manager = DatabaseManager(db_path)
    
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
            
            ParticipantsManager._validate_constraints(participants)
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
    
    def load_from_database(self) -> Dict[str, Participant]:
        """
        Carica i partecipanti dal database.
            
        Returns:
            Dict[str, Participant]: Dizionario dei partecipanti
        """
        try:
            participant_records = self.db_manager.get_participants()
            
            participants = {}
            for record in participant_records:
                # Recupera last_year dal database
                previous_receivers = self.db_manager.get_previous_receivers(record.name, 1)
                last_year = previous_receivers[0] if previous_receivers else ""
                
                participant = Participant(
                    name=record.name,
                    email=record.email,
                    last_year=last_year
                )
                participants[record.name] = participant
            
            self._validate_constraints(participants)
            logger.info(f"Caricati {len(participants)} partecipanti dal database")
            return participants
            
        except Exception as e:
            raise ParticipantsLoadError(f"Errore nel caricamento dal database: {e}") from e
    
    def save_to_database(self, participants: Dict[str, Participant]) -> bool:
        """
        Salva i partecipanti nel database.
        
        Args:
            participants: Dizionario dei partecipanti
            
        Returns:
            True se salvato con successo
        """
        try:
            for participant in participants.values():
                self.db_manager.add_participant(participant.name, participant.email)
            
            logger.info(f"Salvati {len(participants)} partecipanti nel database")
            return True
            
        except Exception as e:
            logger.error(f"Errore nel salvataggio nel database: {e}")
            return False
    
    def migrate_json_to_database(self, json_file: str = "participants.json", year: int = None) -> bool:
        """
        Migra i dati da JSON al database.
        
        Args:
            json_file: File JSON sorgente
            year: Anno da usare per l'estrazione precedente (default: anno corrente)
            
        Returns:
            True se migrazione riuscita
        """
        return self.db_manager.migrate_from_json(json_file, year)
    
    @classmethod  
    def load_from_database_legacy(cls, db_path: str = "secret_santa.db") -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Versione legacy per compatibilità - carica dal database e converte in dizionari.
        
        Args:
            db_path: Percorso del database
            
        Returns:
            Dizionario in formato legacy o None se errore
        """
        try:
            manager = cls(db_path)
            participants = manager.load_from_database()
            
            # Converte da Participant a dict per compatibilità
            return {
                name: {
                    'email': p.email,
                    'last_year': p.last_year,
                    'is_already_extracted': p.is_already_extracted
                }
                for name, p in participants.items()
            }
        except Exception as e:
            logger.error(f"Errore nel caricamento legacy dal database: {e}")
            return None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validazione base dell'email (metodo legacy)."""
        return Participant.validate_email(email)