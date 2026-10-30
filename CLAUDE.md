# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**PulseDeck** è una dashboard di monitoraggio di sistema in tempo reale. Frontend Angular 21 + backend FastAPI: il backend campiona metriche host (CPU, RAM, swap, disco, rete, processi) tramite `psutil` e le espone su un singolo endpoint REST; il frontend fa polling e renderizza tutto in una SPA a tab.

L'applicazione è pensata per girare in locale sulla macchina che si vuole monitorare (Windows in primis — diverse metriche e formattazioni sono Windows-aware).

## Repository layout

Il repository è un mono-repo a due moduli, non un workspace unificato:

- [api.py](api.py) — backend FastAPI mono-file (tutta la logica server in un file)
- [requirements.txt](requirements.txt) — dipendenze Python
- [PulseDeckFE/](PulseDeckFE/) — progetto Angular CLI standalone (nome interno: `pulsedeck-web`)
- [venv/](venv/) — virtualenv Python locale (non committare); il nuovo ambiente verificato è `.venv/` con Python 3.12

## Comandi comuni

### Backend (dalla root del repo)

```powershell
# attivazione venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# installazione dipendenze
pip install -r requirements.txt

# avvio server di sviluppo (porta 8000, reload abilitato)
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Il frontend si aspetta il backend su `/api/metrics (proxy di sviluppo verso http://127.0.0.1:8000)` — vedi [PulseDeckFE/proxy.conf.json](PulseDeckFE/proxy.conf.json). Se cambi porta, aggiorna il target e riavvia Angular. In produzione il server web deve inoltrare `/api` al backend.

### Frontend (da `PulseDeckFE/`)

```powershell
npm install              # solo la prima volta
npm start                # equivalente a `ng serve`, porta 4200
npm run build            # build di produzione → dist/pulsedeck-web
npm run watch            # build incrementale in modalità development
npm test                 # esegue i test Karma/Jasmine
```

Per eseguire un singolo file di test: `ng test --include='**/nome-file.spec.ts'`. Nota: gli schematics di Angular sono configurati con `skipTests: true` ([angular.json:11](PulseDeckFE/angular.json#L11)), quindi i componenti generati con `ng generate` non producono file `.spec.ts` di default.

### Avvio end-to-end tipico

In due terminali separati: backend con `uvicorn` su :8000, frontend con `npm start` su :4200, poi aprire `http://localhost:4200/`. Il `MetricsService` fa il primo fetch immediatamente e poi ogni 1.5 secondi.

## Architettura

### Backend ([api.py](api.py))

Tutto vive in un singolo file. Tre meccanismi importanti da conoscere prima di toccarlo:

1. **Cache statica all'avvio** ([api.py:25-41](api.py#L25-L41)). Hostname, OS, modello CPU, conteggio core, boot time vengono letti una sola volta all'import del modulo e memorizzati nel dict `_STATIC`. Non rileggerli per richiesta — sono invarianti di runtime.

2. **Primer di `cpu_percent`** ([api.py:44](api.py#L44)). La prima chiamata a `psutil.cpu_percent(interval=None)` restituisce sempre 0 perché non ha un campione precedente con cui confrontarsi. Viene "scaldata" all'avvio così la prima richiesta HTTP riceve già valori significativi. Se aggiungi nuove metriche differenziali (qualunque cosa basata su contatori cumulativi), applica lo stesso pattern.

3. **Worker in background per i processi** ([api.py:58-98](api.py#L58-L98)). `psutil.process_iter` con campi tipo `cpu_percent` è molto lento su Windows (centinaia di ms a migliaia, blocca la request). La lista processi viene quindi popolata da un thread daemon che gira ogni 2 secondi e scrive in `_proc_cache` protetto da `_proc_lock`. L'handler legge la cache, non itera mai i processi nel request path. Se aggiungi altre metriche "lente" — segui lo stesso schema.

Altri due dettagli sui contatori differenziali:
- Velocità rete e velocità disco I/O sono calcolate confrontando i contatori della chiamata corrente con quelli memorizzati in `_net_prev` / `_disk_prev` ([api.py:21-22](api.py#L21-L22)). La prima richiesta dopo l'avvio restituisce quindi `"N/A"` per queste velocità — è atteso, non un bug.
- `getloadavg()` non esiste su Windows e viene gestito con un try/except che restituisce `[None, None, None]` ([api.py:120-123](api.py#L120-L123)). Il frontend mostra "non disponibile" in quel caso.

CORS consente per default soltanto le origini localhost/127.0.0.1:4200 per i metodi `GET`; le origini sono configurabili con `PULSEDECK_CORS_ORIGINS` ([api.py:14-19](api.py#L14-L19)) — sufficiente per uso locale, da restringere se mai dovesse essere esposto.

### Frontend ([PulseDeckFE/src/app/](PulseDeckFE/src/app/))

Progetto Angular **19 standalone** (niente `NgModule`). Bootstrap diretto in [main.ts](PulseDeckFE/src/main.ts) con `bootstrapApplication(AppComponent, appConfig)`. La configurazione globale è in [app.config.ts](PulseDeckFE/src/app/app.config.ts) — fornisce solo `provideHttpClient()` e `provideZoneChangeDetection({ eventCoalescing: true })`. Non c'è routing.

Quattro file applicativi, tutto qui:
- [app.component.ts](PulseDeckFE/src/app/app.component.ts) — componente root, stato della tab attiva, helper UI (`barColor`, `cores`)
- [app.component.html](PulseDeckFE/src/app/app.component.html) — template monolitico con sei sezioni `*ngIf` (overview, cpu, memory, storage, network, processes)
- [app.component.scss](PulseDeckFE/src/app/app.component.scss) — tutto lo styling specifico della dashboard
- [metrics.service.ts](PulseDeckFE/src/app/metrics.service.ts) — service `providedIn: 'root'` con le interfacce TypeScript della response e l'observable di polling

**Pattern di polling** ([metrics.service.ts:70-75](PulseDeckFE/src/app/metrics.service.ts#L70-L75)): `timer(0, 1500)` + `exhaustMap(fetch)` + timeout di 8 secondi + `shareReplay({ bufferSize: 1, refCount: true })`. L'observable è creato una sola volta a livello di service e condiviso. `catchError` pubblica il problema su `connectionError$` e restituisce `EMPTY`: il timer riprova automaticamente. Il template mostra il problema anche dopo il primo caricamento e conserva gli ultimi dati. `exhaustMap` evita richieste sovrapposte senza annullare quelle lente.

**Forma del contratto dati**: le interfacce TypeScript in [metrics.service.ts:6-64](PulseDeckFE/src/app/metrics.service.ts#L6-L64) sono il contratto. Devono restare allineate manualmente con il dict restituito da `get_metrics()` in [api.py:201-269](api.py#L201-L269) — non c'è generazione di tipi. Quando aggiungi/modifichi un campo nel backend, aggiorna anche l'interfaccia corrispondente e il template che lo consuma.

**Convenzioni di stile**:
- Tema dark fisso, palette definita inline negli SCSS (sfondo `#0f0f1a`, accent `#4fc3f7`).
- Le barre di percentuale usano `barColor()` con soglie 60/80 (verde/arancio/rosso) — riusa l'helper, non duplicare la logica.
- Le label UI sono in italiano. Mantieni la lingua quando aggiungi nuove sezioni.
- Stile SCSS dei componenti, indentato a 2 spazi, regole short-hand (`display: flex; gap: 4px;` su una sola riga) — è lo stile esistente.

### Flusso dei dati end-to-end

```
psutil → api.py (cache statica + worker processi + diff network/disk)
       → GET /api/metrics (JSON)
       → MetricsService.metrics$ (polling 1.5s, shareReplay)
       → AppComponent.metrics$ | async
       → template con 6 tab
```

Nessun database, nessuna persistenza, nessuna autenticazione: ogni richiesta restituisce lo snapshot live.
