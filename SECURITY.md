# Sicurezza

PulseDeck è un monitor locale, senza autenticazione. L'API rende visibili
hostname, utente, processi, indirizzi di rete e dettagli delle partizioni.
Mantieni il backend su `127.0.0.1`; non esporlo direttamente su Internet.
CORS non è un sistema di autenticazione e non impedisce l'accesso con client non browser.
Per accesso remoto occorre un reverse proxy con autenticazione e TLS e una
configurazione di rete appropriata. Non usare GitHub Pages come hosting dell'API:
una pagina statica non può eseguire FastAPI né leggere le metriche dell'host.

## Segnalare una vulnerabilità

Non aprire issue pubbliche con dettagli sfruttabili, credenziali o dati personali.
Usa la scheda **Security → Advisories → Report a vulnerability** del repository
se la segnalazione privata è abilitata. Se non è disponibile, chiedi ai maintainer
un canale privato tramite un'issue priva dei dettagli tecnici della vulnerabilità.

Il progetto è in fase iniziale: le correzioni sono destinate al branch predefinito,
senza garanzie di supporto per versioni precedenti. Prima di creare una release,
esegui l'audit delle dipendenze e valuta tutti gli avvisi: una build riuscita
non dimostra l'assenza di vulnerabilità.
