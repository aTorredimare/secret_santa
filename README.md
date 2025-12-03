# 🎅 Secret Santa Organizer

Un sistema automatico per organizzare il Secret Santa con gestione completa dei partecipanti, estrazioni intelligenti e invio email automatico.

## 🎯 Caratteristiche Principali

- **📊 Database SQLite**: Gestione persistente di partecipanti e storico estrazioni
- **🧠 Algoritmo Anti-Ripetizioni**: Evita automaticamente abbinamenti degli anni precedenti
- **📧 Invio Email Automatico**: Notifiche personalizzate via SMTP
- **🔄 Migrazione Automatica**: Converte dati JSON esistenti al database
- **🤫 Modalità Silenziosa**: Mantiene il segreto nascondendo gli abbinamenti
- **🧪 Modalità Test**: Simulazione completa senza invio reale

## 🚀 Installazione Rapida

### Prerequisiti
- Python 3.7+
- Account email con accesso SMTP (Gmail consigliato)

### Setup
```bash
git clone https://github.com/aTorredimare/secret_santa.git
cd secret_santa
```

Non servono dipendenze esterne - tutto usa librerie standard Python!

## ⚙️ Configurazione

### 1. Credenziali Email
Crea il file `.env` nella root del progetto:

```
SECRET_SANTA_EMAIL=tuaemail@gmail.com
SECRET_SANTA_PASSWORD=password_app_gmail
```

> **💡 Per Gmail**: Usa una [Password per App](https://support.google.com/accounts/answer/185833), non la password normale del tuo account.

### 2. Partecipanti
Se è la prima volta, crea `participants.json`:

```json
{
    "Andrea": {
        "email": "andrea@esempio.it",
        "last_year": ""
    },
    "Marco": {
        "email": "marco@esempio.it", 
        "last_year": "Andrea"
    },
    "Lucia": {
        "email": "lucia@esempio.it",
        "last_year": "Marco" 
    }
}
```

- **`email`**: Indirizzo email del partecipante (obbligatorio)
- **`last_year`**: Chi ha ricevuto l'anno scorso (opzionale, per evitare ripetizioni)

> Il sistema migrerà automaticamente i dati JSON al database SQLite al primo avvio.

## 🎮 Utilizzo

### Avvio Principale
```bash
python3 estrazioni.py
```

Il programma ti guiderà attraverso:

1. **📋 Caricamento Automatico**: Legge dal database o migra da JSON
2. **🤫 Modalità Silenziosa**: Scegli se nascondere gli abbinamenti
3. **🎲 Estrazione Intelligente**: Genera abbinamenti evitando ripetizioni
4. **👀 Anteprima**: Visualizza risultati (se non in modalità silenziosa)
5. **🧪 Test o Invio**: Scegli tra simulazione o invio reale

### Esempio di Esecuzione
```
🎅 Secret Santa Organizer 2025 🎁
📊 Modalità Database SQLite attivata

📋 Caricamento partecipanti...
✅ Caricati 6 partecipanti dal database

Modalità silenziosa? (s/n, default=s): s
🎲 Creazione abbinamenti...
✅ Abbinamenti creati con successo
🤫 Modalità silenziosa: 6 abbinamenti creati

Modalità test? (non invia email) (s/n, default=s): n
📤 Inizio invio di 6 email...
✅ Email inviata a Andrea...
✅ Email inviata a Marco...
🎉 Tutte le email inviate con successo!
```

## 🗄️ Gestione Database

Il sistema usa SQLite per memorizzare tutto automaticamente. Comandi utili:

### Esportare Partecipanti
```bash
# Esporta partecipanti in formato JSON compatibile
python3 migrate_to_database.py --export participants_backup.json
```

### Esportare Estrazioni
```bash
# Estrazioni dell'anno corrente
python3 migrate_to_database.py --export-extractions extractions_2025.json

# Estrazioni di un anno specifico
python3 migrate_to_database.py --export-extractions extractions_2024.json --year 2024
```

### Migrazione Manuale
```bash
# Migra dati da JSON esistente
python3 migrate_to_database.py --json-file participants.json

# Migra con anno specifico per lo storico
python3 migrate_to_database.py --year 2024
```

## 📧 Template Email

Ogni partecipante riceve automaticamente:

**Oggetto**: 🎅 Secret Santa 2025 🎁

**Corpo**:
```
Ciao [Nome]!

Il tuo destinatario per il Secret Santa di quest'anno è: [Destinatario]

🎁 Ricordati di mantenere il segreto!
🎄 Buone feste!
```

> L'anno nell'oggetto si aggiorna automaticamente ogni anno.

## 🏗️ Struttura Progetto

```
secret_santa/
├── estrazioni.py              # 🚀 Programma principale
├── database_manager.py        # 🗄️ Gestione database SQLite
├── participants_manager.py    # 👥 Gestione partecipanti
├── extractions_manager.py     # 🎲 Algoritmo estrazioni
├── email_manager.py          # 📧 Invio email SMTP
├── migrate_to_database.py    # 🔄 Script migrazione e export
├── config.py                 # ⚙️ Configurazioni
├── exceptions.py             # 🚨 Eccezioni personalizzate
├── participants.json         # 📋 Dati legacy (opzionale)
├── secret_santa.db          # 🗄️ Database SQLite (auto-creato)
└── .env                     # 🔐 Credenziali (non versionare!)
```

## 🎯 Algoritmo Intelligente

Il sistema è progettato per evitare ripetizioni:

1. **📚 Consultazione Storico**: Controlla estrazioni degli ultimi 2 anni
2. **🎲 Estrazione Casuale**: Genera abbinamenti rispettando i vincoli
3. **💾 Salvataggio Automatico**: Memorizza tutto nel database
4. **📊 Tracciamento**: Mantiene storico completo per anni futuri

### Esempio Logica Anti-Ripetizione
```
2024: Andrea → Marco, Marco → Lucia, Lucia → Andrea
2025: Andrea ≠ Marco (evitato!), Andrea → Lucia ✅
```

## 🔧 Configurazione Avanzata

### Personalizzare SMTP
Modifica `config.py` per provider diversi da Gmail:

```python
@dataclass
class SMTPConfig:
    server: str = "smtp.tuoprovider.com"
    port: int = 587
    email_delay: float = 2.0  # Pausa tra email
```

### Personalizzare Algoritmo
```python
@dataclass
class DatabaseConfig:
    years_history: int = 3  # Anni di storico da considerare
```

## 🛠️ Risoluzione Problemi

### Email non inviate
```bash
# Verifica credenziali
echo $SECRET_SANTA_EMAIL
```
- ✅ Usa Password per App Gmail
- ✅ Verifica connessione internet
- ✅ Controlla spam/posta indesiderata

### Estrazione fallisce
```bash
# Troppi vincoli? Riduci anni di storico in config.py
years_history: int = 1
```

### Database corrotto
```bash
# Ricrea da backup JSON
rm secret_santa.db
python3 migrate_to_database.py
```

### Partecipanti senza email
```
# Log mostra:
WARNING - Partecipante [Nome] senza email, saltato
```
Aggiungi email valida nel JSON o database.

## 🎄 Esempi d'Uso

### Prima Volta
```bash
# 1. Crea participants.json con i tuoi amici
# 2. Configura .env con le tue credenziali
# 3. Avvia
python3 estrazioni.py
# Scegli: Modalità silenziosa Sì, Test Sì
```

### Uso Annuale
```bash
# Aggiungi nuovi partecipanti se necessario
python3 estrazioni.py
# Scegli: Modalità silenziosa Sì, Test No (per invio reale)
```

### Backup e Archiviazione
```bash
# Salva estrazioni dell'anno
python3 migrate_to_database.py --export-extractions secret_santa_2025.json

# Backup completo
cp secret_santa.db secret_santa_backup_2025.db
```

## 🔐 Sicurezza

- ✅ **Credenziali**: Caricate da variabili ambiente
- ✅ **Validazione**: Email verificate con regex rigoroso
- ✅ **SMTP Sicuro**: Connessioni cifrate
- ✅ **Database Locale**: Nessun dato in cloud
- ✅ **Git Safe**: `.env` escluso dal version control

## 📚 API Sviluppatori

```python
from database_manager import DatabaseManager
from extractions_manager import ExtractionsManager

# Gestione database
db = DatabaseManager()
db.add_participant("Nome", "email@esempio.it")
participants = db.get_participants()

# Estrazione programmatica
extractor = ExtractionsManager()
assignments = extractor.extract_with_database(
    participant_names=["Alice", "Bob", "Charlie"],
    year=2025,
    years_back=2
)
```

## 🤝 Contribuire

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/amazing-feature`)
3. Commit delle modifiche (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è open source. Sentiti libero di usarlo e modificarlo per le tue esigenze!

## 🎅 Buon Secret Santa!

Divertiti con le tue estrazioni e... ricorda di mantenere il segreto! 🤫🎁

---

*Made with ❤️ for spreading holiday joy*