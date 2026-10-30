# PulseDeck

**Il tuo sistema, a colpo d'occhio.** Dashboard locale per CPU, memoria, dischi,
rete e processi, con backend FastAPI e frontend Angular 21.

[![CI](https://github.com/mgambarrota/PulseDeck/actions/workflows/ci.yml/badge.svg)](https://github.com/mgambarrota/PulseDeck/actions/workflows/ci.yml)
[![Licenza MIT](https://img.shields.io/badge/license-MIT-a6e3bc)](LICENSE)

## Funzionalità

- Sei viste: panoramica, processore, memoria, archiviazione, rete e processi.
- Aggiornamento ogni 1,5 secondi, con timeout ed errori di connessione visibili.
- Storico degli ultimi 32 campioni di CPU e RAM, mantenuto solo nel browser.
- Tema scuro, layout responsive, animazioni e supporto a `prefers-reduced-motion`.
- Top 35 processi per CPU, raccolti in background ogni 2 secondi.
- Metriche opzionali con fallback quando il sistema non le rende disponibili.
- Nessun account o database; nessuna telemetria esterna implementata dall'app.

Pensato per **Windows, Linux e macOS**. Le verifiche locali sono state eseguite
su macOS; la CI definisce test backend per tutti e tre i sistemi. Il risultato
nelle Actions, dopo il push, è la verifica delle singole combinazioni.

## Prerequisiti

- Python **3.11+** (CI su 3.11 e 3.12).
- Node.js **22.12+ nella linea 22.x**, indicato anche in `.nvmrc`, e npm.
- Git. Angular CLI globale non necessaria.

## Avvio locale

```sh
git clone https://github.com/mgambarrota/PulseDeck.git
cd PulseDeck
```

### 1. Backend

Controlla la versione con `python3 --version` (oppure `py --version` su Windows).
Se il comando predefinito punta a una versione vecchia, seleziona esplicitamente
Python 3.11 o successivo quando crei il virtualenv, ad esempio `python3.12 -m venv .venv`.

**macOS / Linux**:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

**Windows (PowerShell)**:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Su Windows non occorre attivare il virtualenv né modificare le policy PowerShell.
Se hai già un ambiente `venv`, puoi usarlo soltanto se creato con Python 3.11 o successivo; reinstalla le dipendenze aggiornate.

### 2. Frontend

In un secondo terminale:

```sh
cd PulseDeckFE
npm ci
npm start
```

Apri **[localhost:4200](http://localhost:4200)**. Arresta ciascun servizio con `Ctrl+C`.

Angular inoltra `/api` a `http://127.0.0.1:8000` tramite
[proxy.conf.json](PulseDeckFE/proxy.conf.json). Se cambi porta al backend,
aggiorna il target del proxy e riavvia `npm start`.

### Se la dashboard non si connette

1. Verifica che il terminale backend mostri l'avvio completato, senza traceback.
2. Apri [localhost:8000/api/metrics](http://localhost:8000/api/metrics): deve restituire JSON.
3. Apri [localhost:4200/api/metrics](http://localhost:4200/api/metrics): deve restituire lo stesso tipo di dati tramite proxy.
4. Se funziona solo la prima URL, verifica il target del proxy e riavvia Angular.

Il polling riprova automaticamente. Una richiesta può durare al massimo 8 secondi;
le richieste non si sovrappongono. In caso di disconnessione i dati precedenti
restano visibili insieme a un avviso.

## API

`GET /api/metrics` restituisce uno snapshot con queste sezioni:

| Campo | Contenuto |
| --- | --- |
| `timestamp` | Data e ora locale dell'host in formato ISO |
| `system` | Hostname, OS, architettura, utente, avvio e uptime |
| `cpu` | Utilizzo, core, frequenze, tempi CPU e contatori |
| `memory` | RAM e swap |
| `storage` | I/O e partizioni accessibili |
| `network` | Traffico, contatori e interfacce |
| `processes` | Fino a 35 processi ordinati per utilizzo CPU |

Schema interattivo: [localhost:8000/docs](http://localhost:8000/docs).
Il contratto frontend è definito in
[metrics.service.ts](PulseDeckFE/src/app/metrics.service.ts).

## Compatibilità e limiti

- Alcune frequenze CPU, partizioni o interfacce non sono leggibili su tutti gli
  host: le metriche opzionali mostrano `N/A` o elenchi vuoti.
- La prima lettura delle velocità rete/disco può mostrare `N/A`, finché manca
  il campione precedente. I primi valori di utilizzo CPU possono essere zero.
- I contatori interrupt/DPC specifici di Windows valgono zero quando assenti.
- I permessi dell'utente limitano i processi visibili; non occorre avviare come
  amministratore per usare la dashboard.
- In container o VM, le metriche si riferiscono all'ambiente visibile a `psutil`,
  non necessariamente all'intera macchina fisica.
- Lo storico del browser si azzera ricaricando la pagina. Non ci sono esportazione
  o conservazione delle metriche.

## Build e utilizzo fuori dallo sviluppo

```sh
cd PulseDeckFE
npm ci
npm run build
```

I file statici sono in `PulseDeckFE/dist/pulsedeck-web/browser/`.
Il server web deve servirli e inoltrare `/api` al backend **sullo stesso dominio**.
Avvia FastAPI senza reload e con un solo worker, perché i contatori sono in memoria:

```sh
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

GitHub ospita il codice; **GitHub Pages da solo non può eseguire il backend**.
Pubblicare il repository non richiede di esporre la dashboard o le metriche.

L'API è priva di autenticazione e contiene dati dell'host. Mantienila su loopback.
Per accesso remoto serve una configurazione dedicata con autenticazione e TLS:
vedi [SECURITY.md](SECURITY.md). Per default CORS consente soltanto
`http://localhost:4200` e `http://127.0.0.1:4200`. Per origini diverse imposta
`PULSEDECK_CORS_ORIGINS` con una lista separata da virgole prima di avviare FastAPI.
Le variabili `.env` non vengono caricate automaticamente.

## Sviluppo e verifiche

```sh
# Dalla root, con virtualenv attivo
python -m unittest discover -s tests -v
python -m compileall -q api.py

# Frontend
cd PulseDeckFE
npm run build
npm test -- --watch=false --browsers=ChromeHeadless
npm audit
```

La [CI](.github/workflows/ci.yml) esegue i test Python su Windows, Linux e macOS e
compila il frontend con Node 22. Dependabot propone aggiornamenti delle dipendenze.
Requisiti Angular: [tabella ufficiale delle versioni](https://angular.dev/reference/versions).
Consulta [CONTRIBUTING.md](CONTRIBUTING.md) per test manuali e convenzioni.

## Struttura

```text
PulseDeck/
├── api.py                  # API, contatori e worker processi
├── requirements.txt
├── tests/                  # Regressioni e fallback cross-platform
├── PulseDeckFE/            # SPA Angular
│   ├── src/app/
│   └── proxy.conf.json
├── .github/                # CI, Dependabot e template
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## Contributi e licenza

Apri una issue per bug o proposte, oppure una pull request seguendo
[CONTRIBUTING.md](CONTRIBUTING.md). Rimuovi dati personali da log e screenshot.
Le vulnerabilità vanno segnalate secondo [SECURITY.md](SECURITY.md).

Distribuito con [licenza MIT](LICENSE). Novità in [CHANGELOG.md](CHANGELOG.md).
