"""
Modulo per la gestione delle estrazioni del Secret Santa.
"""

import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ExtractionsManager:
    """Classe per gestire le estrazioni degli abbinamenti."""
    
    @staticmethod
    def extract(participants_data: Dict[str, Dict[str, Any]], max_attempts: int = 1000) -> Optional[Dict[str, str]]:
        """
        Estrae gli abbinamenti per il Secret Santa con algoritmo ottimizzato.
        
        Args:
            participants_data: Dizionario dei partecipanti
            max_attempts: Numero massimo di tentativi prima di abbandonare
            
        Returns:
            Dict con gli abbinamenti o None se impossibile trovare una soluzione
        """
        logger.info("Inizio estrazione...")
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
                logger.info(f"Estrazione completata al tentativo {attempt + 1}")
                return extracted
        logger.error(f"Impossibile trovare una soluzione valida dopo {max_attempts} tentativi")
        return None