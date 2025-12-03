#!/usr/bin/env python3
"""
Secret Santa Organizer - Programma principale
"""

import logging
import sys
import os
from typing import Dict, Optional
from datetime import datetime

from config import AppConfig
from participants_manager import ParticipantsManager, Participant
from extractions_manager import ExtractionsManager
from email_manager import EmailManager
from database_manager import DatabaseManager
from exceptions import SecretSantaException

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class SecretSantaOrganizer:
    """Coordinatore principale del Secret Santa."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.participants: Dict[str, Participant] = {}
        self.participants_manager = ParticipantsManager(self.config.database.db_path) if self.config.use_database else None
        self.extractions_manager = ExtractionsManager(self.config.database.db_path) if self.config.use_database else None
        self.db_manager = DatabaseManager(self.config.database.db_path) if self.config.use_database else None
        
    def run(self) -> None:
        """Esegue l'intero processo del Secret Santa."""
        try:
            self._load_participants()
            
            silent_mode = self._get_user_preference("Modalità silenziosa? (non mostra abbinamenti)", default=True)
            
            assignments = self._create_assignments()
            self._preview_assignments(assignments, silent_mode)
            
            if self._get_user_preference("Modalità test? (non invia email)", default=True):
                self._test_mode(assignments, silent_mode)
            else:
                self._send_emails(assignments, silent_mode)
                
        except SecretSantaException as e:
            logger.error(f"❌ Errore: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\n👋 Operazione annullata dall'utente")
            sys.exit(0)
        except EOFError:
            logger.info("\n👋 Input terminato, uscita dal programma")
            sys.exit(0)
    
    def _load_participants(self) -> None:
        """Carica i partecipanti dal database o file JSON."""
        logger.info("📋 Caricamento partecipanti...")
        
        if self.config.use_database:
            # Prova a caricare dal database
            try:
                self.participants = self.participants_manager.load_from_database()
                if not self.participants:
                    # Se il database è vuoto, prova la migrazione automatica
                    if os.path.exists(self.config.participants_file):
                        logger.info("Database vuoto, eseguo migrazione automatica da JSON...")
                        if self.participants_manager.migrate_json_to_database(self.config.participants_file):
                            self.participants = self.participants_manager.load_from_database()
                        else:
                            raise SecretSantaException("Migrazione automatica fallita")
                    else:
                        raise SecretSantaException("Database vuoto e nessun file JSON trovato")
                
                # Carica anche formato legacy per compatibilità con email manager
                self.participants_dict = ParticipantsManager.load_from_database_legacy(
                    self.config.database.db_path
                )
                logger.info(f"✅ Caricati {len(self.participants)} partecipanti dal database")
            
            except Exception as e:
                logger.warning(f"Errore caricamento da database: {e}")
                logger.info("Fallback al file JSON...")
                self._load_from_json()
        else:
            self._load_from_json()
    
    def _load_from_json(self) -> None:
        """Carica i partecipanti dal file JSON (metodo legacy)."""
        # Usa il metodo legacy per compatibilità con ExtractionsManager
        participants_dict = ParticipantsManager.load_from_file_legacy(self.config.participants_file)
        if not participants_dict:
            raise SecretSantaException("Impossibile caricare i partecipanti")
        
        # Converte anche in formato Participant per le nuove funzionalità
        self.participants = ParticipantsManager.load_from_file(self.config.participants_file)
        self.participants_dict = participants_dict
        logger.info(f"✅ Caricati {len(self.participants)} partecipanti dal JSON")
    
    def _create_assignments(self) -> Dict[str, str]:
        """Crea gli abbinamenti Secret Santa."""
        logger.info("🎲 Creazione abbinamenti...")
        
        if self.config.use_database and self.extractions_manager:
            # Usa il nuovo algoritmo con database
            participant_names = list(self.participants.keys())
            assignments = self.extractions_manager.extract_with_database(
                participant_names,
                datetime.now().year,
                self.config.max_extraction_attempts,
                self.config.database.years_history
            )
        else:
            # Usa l'algoritmo legacy
            assignments = ExtractionsManager.extract(
                self.participants_dict, 
                self.config.max_extraction_attempts
            )
        
        if not assignments:
            raise SecretSantaException("Impossibile creare abbinamenti validi")
        
        logger.info(f"✅ Abbinamenti creati con successo")
        return assignments
    
    def _get_user_preference(self, prompt: str, default: bool = False) -> bool:
        """Ottiene preferenza utente con default."""
        default_str = "s" if default else "n"
        other_str = "n" if default else "s"
        response = input(f"{prompt} ({default_str}/{other_str}, default={default_str}): ").lower().strip()
        return response == '' or response == default_str
    
    def _preview_assignments(self, assignments: Dict[str, str], silent_mode: bool) -> None:
        """Mostra anteprima abbinamenti."""
        if silent_mode:
            logger.info(f"🤫 Modalità silenziosa: {len(assignments)} abbinamenti creati")
        else:
            print(f"\n{'='*60}")
            print("🎁 ANTEPRIMA ABBINAMENTI SECRET SANTA 2025 🎁")
            print('='*60)
            for giver, receiver in assignments.items():
                print(f"🎅 {giver} -> 🎁 {receiver}")
            print('='*60 + "\n")
    
    def _test_mode(self, assignments: Dict[str, str], silent_mode: bool) -> None:
        """Modalità test senza invio reale."""
        logger.info("🧪 Modalità test - nessuna email verrà inviata")
        for giver_name in assignments:
            logger.info(f"[TEST] 📧 Email preparata per {giver_name}")
        logger.info(f"✅ Test completato: {len(assignments)} email simulate")
    
    def _send_emails(self, assignments: Dict[str, str], silent_mode: bool) -> None:
        """Invia le email reali."""
        email_manager = EmailManager(self.config)
        email_manager.load_credentials()
        
        successful, failed = email_manager.send_all_emails_legacy(assignments, self.participants_dict, silent_mode)
        
        if failed > 0:
            logger.warning(f"⚠️ {failed} email non inviate")
        else:
            logger.info("🎉 Tutte le email inviate con successo!")
    


def main():
    """Funzione principale."""
    config = AppConfig()
    
    print("🎅 Secret Santa Organizer 2025 🎁")
    if config.use_database:
        print("📊 Modalità Database SQLite attivata")
    else:
        print("📄 Modalità file JSON")
    print()
    
    try:
        organizer = SecretSantaOrganizer(config)
        organizer.run()
    except Exception as e:
        logger.error(f"💥 Errore imprevisto: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()