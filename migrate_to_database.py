#!/usr/bin/env python3
"""
Script di migrazione da participants.json al database SQLite.
"""

import logging
import argparse
import sys
import json
from datetime import datetime

from database_manager import DatabaseManager
from participants_manager import ParticipantsManager

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Funzione principale di migrazione."""
    parser = argparse.ArgumentParser(description="Migra i dati da JSON a SQLite")
    parser.add_argument(
        '--json-file', 
        default='participants.json',
        help='File JSON sorgente (default: participants.json)'
    )
    parser.add_argument(
        '--db-file', 
        default='secret_santa.db',
        help='File database SQLite di destinazione (default: secret_santa.db)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=datetime.now().year,
        help='Anno da assegnare ai partecipanti (default: anno corrente)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forza la migrazione anche se il database esiste già'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostra solo le statistiche del database senza migrare'
    )
    parser.add_argument(
        '--export',
        help='Esporta i dati dal database a JSON (specifica il file di output)'
    )
    parser.add_argument(
        '--export-extractions',
        help='Esporta le estrazioni di un anno a JSON (specifica il file di output)'
    )
    
    args = parser.parse_args()
    
    try:
        db_manager = DatabaseManager(args.db_file)
        
        # Se richiesto solo statistiche
        if args.stats:
            show_stats(db_manager)
            return
        
        # Se richiesto export
        if args.export:
            export_to_json(db_manager, args.export, args.year)
            return
        
        # Se richiesto export estrazioni
        if args.export_extractions:
            export_extractions_to_json(db_manager, args.export_extractions, args.year)
            return
        
        # Verifica se il database ha già dati
        if not args.force:
            stats = db_manager.get_stats()
            if stats['total_participants'] > 0:
                logger.warning(f"Il database contiene già {stats['total_participants']} partecipanti")
                response = input("Vuoi continuare comunque? (s/N): ").lower().strip()
                if response != 's':
                    logger.info("Migrazione annullata")
                    return
        
        # Esegui la migrazione
        logger.info(f"Inizio migrazione da {args.json_file} a {args.db_file}")
        logger.info(f"Anno assegnato: {args.year}")
        
        success = db_manager.migrate_from_json(args.json_file, args.year)
        
        if success:
            logger.info("✅ Migrazione completata con successo!")
            
            # Mostra statistiche post-migrazione
            show_stats(db_manager)
            
            # Verifica integrità
            verify_migration(db_manager, args.json_file, args.year)
            
        else:
            logger.error("❌ Migrazione fallita")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n👋 Migrazione interrotta dall'utente")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Errore durante la migrazione: {e}")
        sys.exit(1)


def show_stats(db_manager: DatabaseManager):
    """Mostra le statistiche del database."""
    logger.info("📊 Statistiche del database:")
    stats = db_manager.get_stats()
    
    print(f"\\n{'='*50}")
    print("📊 STATISTICHE DATABASE SECRET SANTA")
    print('='*50)
    print(f"📍 Database: {stats['database_path']}")
    print(f"👥 Totale partecipanti: {stats['total_participants']}")
    print(f"🎲 Totale estrazioni: {stats['total_extractions']}")
    
    print("\\n📅 Partecipanti per anno:")
    for year, count in stats['participants_by_year'].items():
        print(f"  {year}: {count} partecipanti")
    
    print("\\n🎁 Estrazioni per anno:")
    for year, count in stats['extractions_by_year'].items():
        print(f"  {year}: {count} abbinamenti")
    
    print('='*50 + "\\n")


def verify_migration(db_manager: DatabaseManager, json_file: str, year: int):
    """Verifica l'integrità della migrazione."""
    logger.info("🔍 Verifica integrità migrazione...")
    
    try:
        # Carica dati originali
        with open(json_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # Carica dati migrati
        participants = db_manager.get_participants(year)
        
        # Conta partecipanti con email valida nel JSON
        valid_json_participants = {
            name: data for name, data in original_data.items() 
            if data.get('email', '').strip()
        }
        
        # Verifica corrispondenza
        if len(participants) == len(valid_json_participants):
            logger.info(f"✅ Verifica OK: {len(participants)} partecipanti migrati correttamente")
        else:
            logger.warning(
                f"⚠️ Discrepanza: JSON aveva {len(valid_json_participants)} "
                f"partecipanti validi, database ne ha {len(participants)}"
            )
        
        # Verifica email
        json_emails = {data['email'].strip() for data in valid_json_participants.values()}
        db_emails = {p.email for p in participants}
        
        missing_emails = json_emails - db_emails
        if missing_emails:
            logger.warning(f"⚠️ Email mancanti nel database: {missing_emails}")
        else:
            logger.info("✅ Tutte le email migrate correttamente")
        
        # Verifica estrazioni precedenti
        extractions = db_manager.get_extraction_history(year - 1)
        if extractions:
            logger.info(f"✅ Ricostruite {len(extractions)} estrazioni dell'anno {year - 1}")
        
    except Exception as e:
        logger.warning(f"⚠️ Errore durante la verifica: {e}")


def export_to_json(db_manager: DatabaseManager, output_file: str, year: int):
    """Esporta i dati dal database a JSON."""
    logger.info(f"📤 Export dati dal database a {output_file}")
    
    try:
        exported_file = db_manager.export_to_json(year, output_file)
        logger.info(f"✅ Export completato: {exported_file}")
        
        # Mostra preview del file esportato
        with open(exported_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\\n📋 Preview del file esportato ({len(data)} partecipanti):")
        for name, info in list(data.items())[:5]:
            print(f"  {name}: {info['email']}")
        if len(data) > 5:
            print(f"  ... e altri {len(data) - 5} partecipanti")
        
    except Exception as e:
        logger.error(f"❌ Errore durante l'export: {e}")


def export_extractions_to_json(db_manager: DatabaseManager, output_file: str, year: int):
    """Esporta le estrazioni dal database a JSON."""
    logger.info(f"📤 Export estrazioni dell'anno {year} a {output_file}")
    
    try:
        exported_file = db_manager.export_extractions_to_json(year, output_file)
        logger.info(f"✅ Export estrazioni completato: {exported_file}")
        
        # Mostra preview del file esportato
        with open(exported_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\\n🎁 Preview estrazioni {data['year']} ({len(data['assignments'])} abbinamenti):")
        for giver, receiver in list(data['assignments'].items())[:5]:
            print(f"  {giver} → {receiver}")
        if len(data['assignments']) > 5:
            print(f"  ... e altri {len(data['assignments']) - 5} abbinamenti")
        
    except Exception as e:
        logger.error(f"❌ Errore durante l'export estrazioni: {e}")


if __name__ == "__main__":
    print("🎅 Secret Santa - Script di Migrazione Database 🎁\\n")
    main()