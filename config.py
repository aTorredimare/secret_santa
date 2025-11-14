"""
Configurazioni centralizzate per il Secret Santa.
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    """Configurazione SMTP"""
    server: str = "smtp.gmail.com"
    port: int = 465
    email_delay: float = 1.0


@dataclass
class AppConfig:
    """Configurazione dell'applicazione"""
    participants_file: str = "participants.json"
    env_file: str = ".env"
    max_extraction_attempts: int = 1000
    smtp: SMTPConfig = None
    
    def __post_init__(self):
        if self.smtp is None:
            self.smtp = SMTPConfig()


def load_env_variables() -> Dict[str, str]:
    """
    Carica variabili d'ambiente dal file .env o dalle variabili di sistema.
    
    Returns:
        Dict[str, str]: Dizionario con le variabili caricate
    """
    env_vars = {}
    
    # Prima prova dalle variabili di sistema
    env_vars['SECRET_SANTA_EMAIL'] = os.getenv('SECRET_SANTA_EMAIL', '')
    env_vars['SECRET_SANTA_PASSWORD'] = os.getenv('SECRET_SANTA_PASSWORD', '')
    
    # Poi dal file .env se esistente
    env_file = ".env"
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key, value = key.strip(), value.strip()
                        # Non sovrascrivere variabili di sistema se già presenti e non vuote
                        if not env_vars.get(key):
                            env_vars[key] = value
            logger.debug(f"Caricate variabili dal file .env")
        except Exception as e:
            logger.warning(f"Errore nel caricamento del file .env: {e}")
    
    # Filtra le variabili vuote per il logging
    loaded_vars = {k: v for k, v in env_vars.items() if v}
    logger.info(f"Caricate {len(loaded_vars)} variabili d'ambiente")
    
    return env_vars