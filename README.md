# Secret Santa Organizer 🎅

Organizzatore automatico per Secret Santa che gestisce partecipanti, estrazione degli abbinamenti e invio email di notifica.

## 📋 Funzionalità

- **Gestione partecipanti**: Caricamento automatico da file JSON con validazione email
- **Algoritmo di estrazione**: Evita automaticamente abbinamenti dell'anno precedente
- **Invio email**: Notifiche automatiche personalizzate via SMTP
- **Modalità test**: Simulazione completa senza invio reale
- **Modalità silenziosa**: Mantiene il segreto nascondendo gli abbinamenti
- **Logging completo**: Tracciamento dettagliato di tutte le operazioni
- **Gestione errori**: Sistema robusto di error handling

## 🛠 Installazione

### Prerequisiti
- Python 3.7+
- Accesso email SMTP (es. Gmail)

### Setup
```bash
git clone <repository-url>
cd secret_santa
```

Non sono necessarie dipendenze esterne - il progetto usa solo librerie standard Python.

## ⚙️ Configurazione

### 1. Partecipanti
Modifica `participants.json`:

```json
{
    "Nome1": {
        "email": "email1@esempio.it",
        "last_year": "Nome2"
    },
    "Nome2": {
        "email": "email2@esempio.it",
        "last_year": ""
    }
}
```

- `email`: Indirizzo email del partecipante (obbligatorio)
- `last_year`: Chi ha ricevuto l'anno scorso (opzionale, per evitare ripetizioni)

### 2. Credenziali Email
Crea file `.env`:

```
SECRET_SANTA_EMAIL=tuaemail@gmail.com
SECRET_SANTA_PASSWORD=password_app_gmail
```

**Nota per Gmail**: Usa una [Password per App](https://support.google.com/accounts/answer/185833), non la password normale.

## 🚀 Utilizzo

Esegui il programma:
```bash
python estrazioni.py
```

Il programma ti guiderà attraverso:
1. **Caricamento partecipanti** - Lettura e validazione da `participants.json`
2. **Modalità silenziosa** - Scelta se nascondere gli abbinamenti
3. **Estrazione** - Generazione automatica degli abbinamenti
4. **Anteprima** - Visualizzazione risultati (se non silenziosa)
5. **Modalità test/produzione** - Scelta tra simulazione o invio reale
6. **Invio email** - Notifica ai partecipanti

## 📧 Email Template

Ogni partecipante riceve un'email con il seguente template:

```
Oggetto: 🎅 Secret Santa 2024

Ciao [Nome]!

È arrivato il momento del nostro Secret Santa! 🎁

Quest'anno dovrai fare un regalo a: **[Nome Destinatario]**

Ricorda di mantenere il segreto fino al giorno dello scambio!

Buon divertimento! 🎄
```

## 🏗 Struttura Progetto

```
secret_santa/
├── estrazioni.py              # Entry point principale
├── participants_manager.py    # Gestione partecipanti
├── extractions_manager.py     # Algoritmo estrazione
├── email_manager.py          # Invio email SMTP
├── config.py                 # Configurazioni
├── exceptions.py             # Eccezioni custom
├── participants.json         # Database partecipanti
└── .env                     # Credenziali (non versionare!)
```

## 🔍 Componenti Principali

### SecretSantaOrganizer
Coordinatore principale che orchestra l'intero flusso.

### ParticipantsManager
- Carica partecipanti da JSON
- Valida indirizzi email
- Gestisce errori di formato

### ExtractionsManager
- Algoritmo di estrazione con retry
- Evita abbinamenti ripetuti
- Gestisce casi limite (piccoli gruppi)

### EmailManager
- Connessione SMTP sicura
- Invio con retry automatico
- Template email personalizzati

## 🚨 Gestione Errori

Eccezioni specializzate per ogni tipo di problema:

- `ParticipantsLoadError` - Errori caricamento file
- `ExtractionError` - Impossibilità di trovare abbinamenti validi
- `EmailError` - Problemi invio email
- `ValidationError` - Dati non validi

## 🛡 Sicurezza

- Credenziali caricate da variabili ambiente
- Validazione rigorosa email con regex
- Connessioni SMTP sicure
- File `.env` escluso da version control

## 🧪 Test e Debug

### Modalità Test
- Simula invio senza spedire email
- Verifica configurazione
- Debug flusso completo

### Logging
Log strutturato con:
- Timestamp
- Livello (INFO/WARNING/ERROR)
- Modulo di origine
- Messaggio dettagliato

## 💡 Esempi d'Uso

### Primo avvio
```bash
python estrazioni.py
# Scegli modalità silenziosa: Sì
# Scegli modalità test: Sì (per sicurezza)
```

### Invio reale
```bash
python estrazioni.py
# Modalità silenziosa: Sì
# Modalità test: No
# Conferma invio email
```

## 🔧 Personalizzazioni

### Configurazione SMTP
Modifica `config.py` per provider diversi da Gmail:

```python
@dataclass
class SMTPConfig:
    server: str = "smtp.tuoprovider.com"
    port: int = 587
    email_delay: float = 2.0
```

### Template Email
Personalizza il messaggio in `email_manager.py`:

```python
def _create_message_body(self, receiver_name: str) -> str:
    return f"""
    Il tuo messaggio personalizzato per {receiver_name}
    """
```

## ❓ Risoluzione Problemi

**Estrazione fallisce sempre**
- Verifica che non ci siano troppi vincoli `last_year`
- Con meno di 3 partecipanti è difficile evitare ripetizioni

**Email non inviate**
- Controlla credenziali in `.env`
- Per Gmail, usa Password per App
- Verifica connessione internet

**Errori di validazione**
- Controlla formato email in `participants.json`
- Verifica sintassi JSON

## 📝 Changelog

### v1.0
- Implementazione base con estrazione e invio email
- Modalità test e silenziosa
- Gestione errori completa
- Logging strutturato

---
🎄 **Buon Secret Santa a tutti!** 🎁
