"""
Modulo per la gestione delle estrazioni del Secret Santa.
"""

import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ExtractionsManager:
    """Classe per gestire le estrazioni degli abbinamenti con supporto database."""
    
    def __init__(self, db_path: str = "secret_santa.db"):
        """Inizializza il manager con database."""
        self.db_manager = DatabaseManager(db_path)
    
    def extract_with_database(self, participants_names: list, year: int = None, 
                             max_attempts: int = 1000, years_back: int = 2) -> Optional[Dict[str, str]]:
        """
        Estrae gli abbinamenti utilizzando lo storico del database.
        
        Args:
            participants_names: Lista nomi partecipanti
            year: Anno dell'estrazione (default: anno corrente)
            max_attempts: Numero massimo di tentativi
            years_back: Anni di storico da considerare per evitare ripetizioni
            
        Returns:
            Dict con gli abbinamenti o None se impossibile
        """
        if year is None:
            year = datetime.now().year
            
        logger.info(f"Inizio estrazione per l'anno {year} con {len(participants_names)} partecipanti...")
        
        for attempt in range(max_attempts):
            extracted = {}
            success = True
            already_extracted = set()
            shuffled_names = participants_names.copy()
            random.shuffle(shuffled_names)
            
            for giver in shuffled_names:
                # Recupera i destinatari precedenti dal database
                previous_receivers = set(self.db_manager.get_previous_receivers(giver, years_back))
                
                # Trova destinatari disponibili
                available_receivers = [
                    name for name in participants_names
                    if (name not in already_extracted and 
                        name != giver and 
                        name not in previous_receivers)
                ]
                
                if not available_receivers:
                    success = False
                    break
                    
                receiver = random.choice(available_receivers)
                already_extracted.add(receiver)
                extracted[giver] = receiver
            
            if success:
                # Salva l'estrazione nel database
                if self.db_manager.save_extraction(year, extracted):
                    logger.info(f"Estrazione completata e salvata al tentativo {attempt + 1}")
                    return extracted
                else:
                    logger.warning("Estrazione completata ma non salvata nel database")
                    return extracted
        
        logger.error(f"Impossibile trovare una soluzione valida dopo {max_attempts} tentativi")
        return None
    
    def get_extraction_history(self, year: int = None) -> Dict[str, str]:
        """
        Recupera l'estrazione salvata per un anno specifico.
        
        Args:
            year: Anno di interesse (default: anno corrente)
            
        Returns:
            Dizionario degli abbinamenti
        """
        if year is None:
            year = datetime.now().year
            
        extractions = self.db_manager.get_extraction_history(year)
        return {extraction.giver_name: extraction.receiver_name for extraction in extractions}
    
    def mark_extraction_completed(self, year: int, giver_name: str) -> bool:
        """
        Marca un'estrazione come completata.
        
        Args:
            year: Anno dell'estrazione
            giver_name: Nome del partecipante
            
        Returns:
            True se marcata con successo
        """
        return self.db_manager.mark_extraction_completed(year, giver_name)
    
    @staticmethod
    def extract(participants_data: Dict[str, Dict[str, Any]], max_attempts: int = 1000) -> Optional[Dict[str, str]]:
        """
        Estrae gli abbinamenti per il Secret Santa con algoritmo ottimizzato (metodo legacy).
        
        Args:
            participants_data: Dizionario dei partecipanti
            max_attempts: Numero massimo di tentativi prima di abbandonare
            
        Returns:
            Dict con gli abbinamenti o None se impossibile trovare una soluzione
        """
        logger.info("Inizio estrazione (metodo legacy)...")
        names = list(participants_data.keys())
        
        for attempt in range(max_attempts):
            for participant in participants_data.values():
                participant["is_already_extracted"] = False
            
            extracted = {}
            success = True            
            shuffled_names = names.copy()
            random.shuffle(shuffled_names)
            
            for giver in shuffled_names:
                available_receivers = [
                    name for name in names 
                    if (not participants_data[name]["is_already_extracted"] and 
                        name != giver and 
                        (participants_data[giver]["last_year"] == "" or participants_data[giver]["last_year"] != name))
                ]
                
                if not available_receivers:
                    success = False
                    break
                receiver = random.choice(available_receivers)
                participants_data[receiver]["is_already_extracted"] = True
                extracted[giver] = receiver
            
            if success:
                logger.info(f"Estrazione completata al tentativo {attempt + 1} (metodo legacy)")
                return extracted
        logger.error(f"Impossibile trovare una soluzione valida dopo {max_attempts} tentativi (metodo legacy)")
        return None