"""
Modulo per la gestione dell'invio delle email del Secret Santa.
"""

import smtplib
import time
import logging
import getpass
from datetime import datetime
from typing import Dict, Tuple, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import AppConfig, load_env_variables
from exceptions import EmailError
from participants_manager import Participant

logger = logging.getLogger(__name__)


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """
    Carica le variabili dal file .env
    
    Args:
        env_path: Percorso del file .env
        
    Returns:
        Dizionario con le variabili caricate
    """
    env_vars = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        logger.info(f"Caricate {len(env_vars)} variabili da {env_path}")
        return env_vars
    except FileNotFoundError:
        logger.warning(f"File {env_path} non trovato")
        return {}
    except Exception as e:
        logger.error(f"Errore nel caricamento del file .env: {e}")
        return {}


class EmailManager:
    """Classe per gestire l'invio delle email con retry e validazione."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.sender_email: Optional[str] = None
        self.sender_password: Optional[str] = None
    
    def load_credentials(self) -> Tuple[str, str]:
        """Carica credenziali con fallback sicuro."""
        env_vars = load_env_variables()
        
        sender_email = env_vars.get('SECRET_SANTA_EMAIL')
        password = env_vars.get('SECRET_SANTA_PASSWORD')
        
        if not sender_email:
            logger.info("Email non trovata nelle variabili d'ambiente")
            sender_email = input("Inserisci l'email del mittente: ").strip()
            if not Participant.validate_email(sender_email):
                raise EmailError("Email del mittente non valida")
        else:
            logger.info(f"Email caricata dalle variabili d'ambiente: {sender_email}")
        
        if not password:
            logger.info("Password non trovata nelle variabili d'ambiente")
            password = getpass.getpass("Inserisci la password dell'email: ")
            if not password:
                raise EmailError("Password non può essere vuota")
        else:
            logger.info("Password caricata dalle variabili d'ambiente")
        
        self.sender_email = sender_email
        self.sender_password = password
        return sender_email, password
    
    def _create_email_message(self, receiver_email: str, giver_name: str, receiver_name: str) -> MIMEMultipart:
        """Crea un messaggio email strutturato."""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "🎅 Secret Santa 2025 🎁"
        
        body = f"""Ciao {giver_name},
    Il tuo destinatario per il Secret Santa di quest'anno è: {receiver_name}
    🎁 Ricordati di mantenere il segreto!
    🎄 Buone feste!
        
    ---
    Questo è un messaggio automatico del sistema Secret Santa.
    """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        return msg
    
    def send_single_email(self, participant: Participant, receiver_name: str, 
                         max_retries: int = 3) -> bool:
        """Invia una singola email con retry automatico."""
        if not self.sender_email or not self.sender_password:
            raise EmailError("Credenziali non caricate")
        
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP_SSL(self.config.smtp.server, self.config.smtp.port) as server:
                    server.login(self.sender_email, self.sender_password)
                    
                    msg = self._create_email_message(
                        participant.email, 
                        participant.name, 
                        receiver_name
                    )
                    
                    server.send_message(msg)
                    logger.info(f"✅ Email inviata a {participant.name} (tentativo {attempt + 1})")
                    return True
                    
            except smtplib.SMTPAuthenticationError as e:
                logger.error("❌ Errore di autenticazione SMTP")
                raise EmailError("Credenziali email non valide") from e
            except Exception as e:
                logger.warning(f"⚠️ Tentativo {attempt + 1} fallito per {participant.name}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff esponenziale
                
        logger.error(f"❌ Invio fallito per {participant.name} dopo {max_retries} tentativi")
        return False
    
    def send_all_emails(self, assignments: Dict[str, str], 
                       participants: Dict[str, Participant], 
                       silent_mode: bool = False) -> Tuple[int, int]:
        """Invia tutte le email con gestione errori migliorata."""
        if not assignments:
            raise EmailError("Nessun abbinamento da inviare")
        
        successful = 0
        failed = 0
        
        logger.info(f"📤 Inizio invio di {len(assignments)} email...")
        
        for giver_name, receiver_name in assignments.items():
            try:
                participant = participants[giver_name]
                
                if not silent_mode:
                    logger.info(f"📧 Invio a {giver_name} -> {receiver_name}")
                else:
                    logger.info(f"📧 Invio a {giver_name}...")
                
                if self.send_single_email(participant, receiver_name):
                    successful += 1
                else:
                    failed += 1
                
                time.sleep(self.config.smtp.email_delay)
                
            except Exception as e:
                logger.error(f"❌ Errore imprevisto per {giver_name}: {e}")
                failed += 1
        
        logger.info(f"🎯 Completato: {successful} riusciti, {failed} falliti")
        return successful, failed
    
    # Metodi legacy per compatibilità
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validazione base dell'email (metodo legacy)."""
        return Participant.validate_email(email)
    
    def send_single_email_legacy(self, receiver_email: str, subject: str, body: str) -> bool:
        """Versione legacy del metodo per compatibilità."""
        if not self.sender_email or not self.sender_password:
            logger.error("Credenziali email non caricate")
            return False
            
        if not self.validate_email(receiver_email):
            logger.error(f"Email non valida: {receiver_email}")
            return False
        
        try:
            with smtplib.SMTP_SSL(self.config.smtp.server, self.config.smtp.port) as server:
                server.login(self.sender_email, self.sender_password)
                message = f"Subject: {subject}\n\n{body}".encode("utf-8")
                server.sendmail(self.sender_email, receiver_email, message)
                logger.info(f"Email inviata con successo a {receiver_email}")
                return True
        except smtplib.SMTPAuthenticationError:
            logger.error("Errore di autenticazione SMTP. Verifica email e password.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Errore SMTP: {e}")
            return False
    def send_all_emails_legacy(self, extracted: Dict[str, str], participants: Dict[str, Dict], 
                              silent_mode: bool = False) -> Tuple[int, int]:
        """Versione legacy per compatibilità con il codice esistente."""
        if not self.sender_email or not self.sender_password:
            logger.error("Credenziali email non caricate")
            return 0, len(extracted)
        
        successful_sends = 0
        failed_sends = 0
        
        logger.info(f"📤 Inizio invio di {len(extracted)} email...")
        
        for giver, receiver in extracted.items():
            email_body = f"""Ciao {giver}!
    È arrivato il momento del nostro Secret Santa! 🎁
            
    Quest'anno dovrai fare un regalo a: **{receiver}**
            
    Ricorda di mantenere il segreto fino al giorno dello scambio!
    Buon divertimento! 🎄
    """
            
            logger.info(f"📧 Invio email a {giver} ({participants[giver]['email']})...")
            
            current_year = datetime.now().year
            if self.send_single_email_legacy(participants[giver]["email"], f"🎅 Secret Santa {current_year}", email_body):
                successful_sends += 1
                if silent_mode:
                    logger.info(f"✅ Email inviata con successo a {giver}")
            else:
                failed_sends += 1
                logger.error(f"❌ Invio fallito per {giver}")
            
            time.sleep(self.config.smtp.email_delay)
        
        logger.info(f"🎯 Invio completato: {successful_sends} riusciti, {failed_sends} falliti")
        return successful_sends, failed_sends