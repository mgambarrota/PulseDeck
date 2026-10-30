# Prima pubblicazione

## Preparazione locale

- [ ] Rivedere i file modificati, inclusa la scelta della licenza MIT e l'attribuzione.
- [x] Test backend e build frontend verificati localmente con Python 3.12 e Node 22.
- [x] Test polling, timeout e riconnessione superati in ChromeHeadless.
- [x] Audit npm e Python senza vulnerabilità note alla verifica locale del 30 ottobre 2026.
- [ ] Eseguire `npm audit` e verificare gli avvisi ancora aperti; non usare `--force` senza valutare le migrazioni richieste.
- [ ] Verificare il layout delle sei viste su desktop e mobile e la riconnessione API.
- [ ] Controllare i file da includere: niente ambienti, credenziali, metriche o screenshot personali.

## Su GitHub

- [ ] Fare commit e push delle modifiche sul repository desiderato.
- [ ] Verificare che tutte le combinazioni della CI siano verdi.
- [ ] Impostare descrizione e topic del repository (es. system-monitor, fastapi, angular, psutil).
- [ ] Abilitare segnalazioni private delle vulnerabilità e avvisi Dependabot nelle impostazioni del repository.
- [ ] Configurare protezione del branch predefinito e richiedere la CI prima del merge, se desiderato.
- [ ] Verificare diritti e consenso alla pubblicazione anche per i contenuti presenti nella cronologia Git.
- [ ] Rendere pubblico il repository quando pronto. La pubblicazione del codice non richiede di esporre l'API.

## Prima release

- [ ] Risolvere o valutare esplicitamente gli avvisi di sicurezza residui, incluse eventuali migrazioni Angular.
- [ ] Aggiornare `CHANGELOG.md` con la data effettiva della release.
- [ ] Verificare che versione API, package.json e lockfile coincidano.
- [ ] Creare il tag `v0.1.0` e una release con istruzioni e limiti noti.

Questi passaggi GitHub non vengono eseguiti automaticamente dai file del repository.
