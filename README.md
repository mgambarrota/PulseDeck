# PulseDeck

Dashboard di monitoraggio di sistema in tempo reale. Un backend FastAPI campiona le metriche dell'host tramite `psutil` e un frontend Angular 19 le visualizza in una SPA a tab con aggiornamento continuo.

Pensato per girare in locale sulla macchina da monitorare. Funziona su **Windows, Linux e macOS** senza modifiche al codice.

## Cosa mostra

Sei viste, una per tab:

- **Overview** — riepilogo sistema e barre di utilizzo CPU/RAM/SWAP
- **CPU** — modello, frequenze, core fisici/logici, utilizzo per-core, tempi CPU, context switch, interrupts, load average
- **Memory** — dettaglio RAM e SWAP (totale, usata, libera, disponibile)
- **Storage** — velocità I/O istantanea, totali letti/scritti, utilizzo per ogni partizione
- **Network** — velocità upload/download, contatori pacchetti/errori/drop, dettaglio per ogni interfaccia (IPv4, IPv6, MAC, stato, MTU)
- **Processes** — top 35 processi ordinati per CPU%, con PID, nome, stato, RAM, thread, utente

I dati vengono aggiornati ogni 1.5 secondi.

## Stack tecnico

| Componente | Tecnologia |
|------------|------------|
| Backend    | Python 3 + FastAPI + Uvicorn + psutil |
| Frontend   | Angular 19 (standalone, senza NgModule) + RxJS + SCSS |
| Trasporto  | REST/JSON, polling HTTP |

## Struttura del repository

```
dashboard/
├── api.py              # backend FastAPI mono-file
├── requirements.txt    # dipendenze Python
├── PulseDeckFE/        # frontend Angular
│   └── src/app/        # AppComponent + MetricsService
└── README.md
```

## Avvio rapido

### 1. Prerequisiti

- Python 3.9+
- Node.js 18+ e npm
- Angular CLI (`npm install -g @angular/cli`) — opzionale, gli script npm bastano

### 2. Backend

Dalla root del repository:

```powershell
# crea ed attiva il virtualenv (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# installa le dipendenze
pip install -r requirements.txt

# avvia il server (porta 8000)
python -m uvicorn api:app --reload --port 8000
```

Su Linux/macOS sostituisci l'attivazione con `source venv/bin/activate`.

### 3. Frontend

In un secondo terminale, dalla cartella `PulseDeckFE/`:

```bash
npm install      # solo la prima volta
npm start        # serve su http://localhost:4200
```

Apri il browser su [http://localhost:4200](http://localhost:4200). Il frontend cerca il backend su `http://localhost:8000` — se cambi porta, aggiornala in [PulseDeckFE/src/app/metrics.service.ts](PulseDeckFE/src/app/metrics.service.ts).

## API

Un solo endpoint:

### `GET /api/metrics`

Restituisce uno snapshot JSON con la struttura:

```json
{
  "timestamp": "2026-05-20T12:34:56.789",
  "system":  { "hostname": "...", "os": "...", "uptime": "...", ... },
  "cpu":     { "total_percent": 12.3, "per_core": [...], ... },
  "memory":  { "ram_total": "16.0 GB", "ram_percent": 42, ... },
  "storage": { "read_speed": "1.2 MB/s", "partitions": [...] },
  "network": { "upload_speed": "120.5 KB/s", "interfaces": [...] },
  "processes": [ { "pid": 1234, "name": "...", "cpu_percent": 8.4, ... } ]
}
```

Lo schema completo è definito (lato TypeScript) in [PulseDeckFE/src/app/metrics.service.ts](PulseDeckFE/src/app/metrics.service.ts).

CORS è aperto a `*` per i soli metodi `GET`: adatto a uso locale, da restringere se si decide di esporre il servizio.

## Build di produzione

```bash
cd PulseDeckFE
npm run build      # output → dist/pulsedeck-web
```

Il backend va eseguito senza `--reload` in produzione (es. `uvicorn api:app --host 0.0.0.0 --port 8000`).

## Note di compatibilità

L'app è multi-piattaforma, ma alcune metriche dipendono dal sistema operativo:

- **`load average`** (1/5/15 min) — disponibile solo su Linux/macOS. Su Windows il frontend mostra "non disponibile".
- **`cpu_times.interrupt` e `cpu_times.dpc`** — disponibili solo su Windows; altrove valgono 0.
- **Velocità rete e I/O disco** — sono calcolate per differenza tra due campionamenti, quindi la prima richiesta subito dopo l'avvio restituisce `"N/A"` finché non c'è un campione precedente.
- **Lista processi** — su Windows `psutil.process_iter` è lento, perciò il backend la aggiorna in un thread di background ogni 2 secondi e la espone via cache.
