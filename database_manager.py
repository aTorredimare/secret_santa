"""
Modulo per la gestione del database SQLite del Secret Santa.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from contextlib import contextmanager

from exceptions import ValidationError, ParticipantsLoadError

logger = logging.getLogger(__name__)


@dataclass
class ParticipantRecord:
    """Record di un partecipante nel database."""
    id: Optional[int]
    name: str
    email: str
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class ExtractionRecord:
    """Record di un'estrazione nel database."""
    id: Optional[int]
    year: int
    giver_name: str
    receiver_name: str
    extraction_date: datetime
    is_completed: bool = False


class DatabaseManager:
    """Gestisce tutte le operazioni sul database SQLite."""
    
    def __init__(self, db_path: str = "secret_santa.db"):
        """
        Inizializza il manager del database.
        
        Args:
            db_path: Percorso del file database SQLite
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Inizializza il database creando le tabelle se non esistono."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabella partecipanti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabella estrazioni
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extractions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    giver_name TEXT NOT NULL,
                    receiver_name TEXT NOT NULL,
                    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_completed BOOLEAN DEFAULT 0,
                    UNIQUE(year, giver_name)
                )
            """)
            
            # Indici per performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_participants_active ON participants(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_extractions_year ON extractions(year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_extractions_giver ON extractions(giver_name)")
            
            conn.commit()
            logger.info("Database inizializzato con successo")
    
    @contextmanager
    def _get_connection(self):
        """Context manager per connessioni database con gestione errori."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Abilita accesso per nome colonna
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Errore database: {e}")
            raise ValidationError(f"Errore database: {e}") from e
        finally:
            if conn:
                conn.close()
    
    def add_participant(self, name: str, email: str) -> int:
        """
        Aggiunge un partecipante al database.
        
        Args:
            name: Nome del partecipante
            email: Email del partecipante
            
        Returns:
            ID del partecipante inserito
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO participants (name, email)
                VALUES (?, ?)
            """, (name, email))
            conn.commit()
            participant_id = cursor.lastrowid
            logger.info(f"Partecipante {name} aggiunto/aggiornato")
            return participant_id
    
    def get_participants(self, active_only: bool = True) -> List[ParticipantRecord]:
        """
        Recupera i partecipanti.
        
        Args:
            active_only: Se True, recupera solo partecipanti attivi
            
        Returns:
            Lista di record partecipanti
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM participants"
            params = []
            
            if active_only:
                query += " WHERE is_active = 1"
            
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            participants = []
            for row in rows:
                participant = ParticipantRecord(
                    id=row['id'],
                    name=row['name'],
                    email=row['email'],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                )
                participants.append(participant)
            
            logger.info(f"Recuperati {len(participants)} partecipanti")
            return participants
    
    def save_extraction(self, year: int, assignments: Dict[str, str]) -> bool:
        """
        Salva un'estrazione completa nel database.
        
        Args:
            year: Anno dell'estrazione
            assignments: Dizionario giver -> receiver
            
        Returns:
            True se salvata con successo
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Prima rimuovi eventuali estrazioni esistenti per quell'anno
                cursor.execute("DELETE FROM extractions WHERE year = ?", (year,))
                
                # Inserisci le nuove estrazioni
                extraction_data = [
                    (year, giver, receiver, datetime.now().isoformat(), False)
                    for giver, receiver in assignments.items()
                ]
                
                cursor.executemany("""
                    INSERT INTO extractions (year, giver_name, receiver_name, extraction_date, is_completed)
                    VALUES (?, ?, ?, ?, ?)
                """, extraction_data)
                
                conn.commit()
                logger.info(f"Salvata estrazione per l'anno {year} con {len(assignments)} abbinamenti")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Errore nel salvataggio estrazione: {e}")
                return False
    
    def get_previous_receivers(self, giver_name: str, years_back: int = 3) -> List[str]:
        """
        Recupera i destinatari degli ultimi anni per un partecipante.
        
        Args:
            giver_name: Nome del partecipante
            years_back: Quanti anni indietro controllare
            
        Returns:
            Lista dei nomi dei destinatari precedenti
        """
        current_year = datetime.now().year
        start_year = current_year - years_back
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT receiver_name FROM extractions 
                WHERE giver_name = ? AND year >= ? AND year < ?
                ORDER BY year DESC
            """, (giver_name, start_year, current_year))
            
            rows = cursor.fetchall()
            previous_receivers = [row['receiver_name'] for row in rows]
            
            logger.debug(f"Destinatari precedenti per {giver_name}: {previous_receivers}")
            return previous_receivers
    
    def get_extraction_history(self, year: int = None) -> List[ExtractionRecord]:
        """
        Recupera lo storico delle estrazioni.
        
        Args:
            year: Anno specifico (default: tutti gli anni)
            
        Returns:
            Lista di record estrazioni
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if year:
                cursor.execute("""
                    SELECT * FROM extractions WHERE year = ?
                    ORDER BY extraction_date DESC
                """, (year,))
            else:
                cursor.execute("""
                    SELECT * FROM extractions 
                    ORDER BY year DESC, extraction_date DESC
                """)
            
            rows = cursor.fetchall()
            
            extractions = []
            for row in rows:
                extraction = ExtractionRecord(
                    id=row['id'],
                    year=row['year'],
                    giver_name=row['giver_name'],
                    receiver_name=row['receiver_name'],
                    extraction_date=datetime.fromisoformat(row['extraction_date']),
                    is_completed=bool(row['is_completed'])
                )
                extractions.append(extraction)
            
            logger.info(f"Recuperate {len(extractions)} estrazioni dallo storico")
            return extractions
    
    def mark_extraction_completed(self, year: int, giver_name: str) -> bool:
        """
        Marca un'estrazione come completata.
        
        Args:
            year: Anno dell'estrazione
            giver_name: Nome del partecipante che ha completato
            
        Returns:
            True se aggiornata con successo
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE extractions 
                SET is_completed = 1 
                WHERE year = ? AND giver_name = ?
            """, (year, giver_name))
            
            conn.commit()
            success = cursor.rowcount > 0
            
            if success:
                logger.info(f"Estrazione marcata come completata per {giver_name} ({year})")
            else:
                logger.warning(f"Nessuna estrazione trovata per {giver_name} ({year})")
            
            return success
    
    def migrate_from_json(self, json_file: str = "participants.json", year: int = None) -> bool:
        """
        Migra i dati dal file JSON al database.
        
        Args:
            json_file: Percorso del file JSON
            year: Anno da usare per l'estrazione precedente (default: anno corrente)
            
        Returns:
            True se migrazione riuscita
        """
        if year is None:
            year = datetime.now().year
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                participants_data = json.load(f)
            
            migrated_count = 0
            previous_year_assignments = {}
            
            # Prima, aggiungi tutti i partecipanti
            for name, data in participants_data.items():
                email = data.get('email', '').strip()
                if not email:
                    logger.warning(f"Partecipante {name} senza email, saltato")
                    continue
                
                self.add_participant(name, email)
                migrated_count += 1
                
                # Raccogli info per ricostruire l'estrazione dell'anno precedente
                last_year_receiver = data.get('last_year', '').strip()
                if last_year_receiver:
                    previous_year_assignments[name] = last_year_receiver
            
            # Se abbiamo dati dell'anno precedente, salvali
            if previous_year_assignments:
                self.save_extraction(year - 1, previous_year_assignments)
                logger.info(f"Ricostruita estrazione dell'anno {year - 1} da last_year")
            
            logger.info(f"Migrazione completata: {migrated_count} partecipanti")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante la migrazione: {e}")
            return False
    
    def export_to_json(self, year: int = None, output_file: str = None) -> str:
        """
        Esporta i dati del database in formato JSON.
        
        Args:
            year: Anno delle estrazioni da considerare per last_year (default: anno corrente)
            output_file: File di output (default: participants.json)
            
        Returns:
            Percorso del file creato
        """
        if year is None:
            year = datetime.now().year
        
        if output_file is None:
            output_file = f"participants.json"
        
        participants = self.get_participants()
        previous_extractions = self.get_extraction_history(year - 1)
        
        # Crea un dizionario per i destinatari dell'anno precedente
        last_year_map = {}
        for extraction in previous_extractions:
            last_year_map[extraction.giver_name] = extraction.receiver_name
        
        # Costruisci il JSON in formato compatibile
        export_data = {}
        for participant in participants:
            export_data[participant.name] = {
                'email': participant.email,
                'last_year': last_year_map.get(participant.name, '')
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Esportati {len(participants)} partecipanti in {output_file}")
        return output_file
    
    def export_extractions_to_json(self, year: int = None, output_file: str = None) -> str:
        """
        Esporta le estrazioni di un anno in formato JSON.
        
        Args:
            year: Anno delle estrazioni da esportare (default: anno corrente)
            output_file: File di output (default: extractions_[year].json)
            
        Returns:
            Percorso del file creato
        """
        if year is None:
            year = datetime.now().year
        
        if output_file is None:
            output_file = f"extractions_{year}.json"
        
        extractions = self.get_extraction_history(year)
        
        # Converte in formato JSON
        export_data = {
            "year": year,
            "extraction_date": extractions[0].extraction_date.isoformat() if extractions else None,
            "assignments": {
                extraction.giver_name: extraction.receiver_name 
                for extraction in extractions
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Esportate {len(extractions)} estrazioni dell'anno {year} in {output_file}")
        return output_file