# Contribuire a PulseDeck

Sono benvenuti bug report, miglioramenti alla UI e correzioni di compatibilità.
Per iniziare segui il [README](README.md), crea un branch dal branch predefinito
e mantieni ogni pull request concentrata su un problema concreto.

## Verifiche prima di una pull request

Dalla root, con il virtualenv attivo:

```sh
python -m unittest discover -s tests -v
python -m compileall -q api.py
```

Per il frontend:

```sh
cd PulseDeckFE
npm ci
npm run build
npm test -- --watch=false --browsers=ChromeHeadless
```

Verifica manualmente le sei viste, la riconnessione con API spenta e riaccesa,
il layout mobile e la preferenza `prefers-reduced-motion`. Indica nella PR cosa
hai effettivamente provato: i test simulati non sostituiscono una prova su un OS reale.
La CI esegue i test backend su Windows, Linux e macOS e compila Angular e verifica polling, timeout e riconnessione con ChromeHeadless.
Per i test frontend locali occorre Chrome installato.

## Convenzioni

- Mantieni le etichette dell'interfaccia in italiano.
- Gestisci i contatori opzionali senza far fallire l'intero snapshot.
- Mantieni la raccolta dei processi fuori dal percorso HTTP.
- Aggiorna insieme `api.py` e le interfacce in `metrics.service.ts`.
- Conserva il lockfile npm e usa `npm ci` per installazioni riproducibili.
- Non includere `venv`, `node_modules`, build o metriche personali nei commit.
- Usa test per regressioni e comportamento significativo.

Per segnalare bug includi passaggi riproducibili, OS e versioni runtime, rimuovendo
i dati personali dai log. Per vulnerabilità segui [SECURITY.md](SECURITY.md).

Mantieni le discussioni rispettose, tecniche e inclusive. I contributi sono
forniti sotto la [licenza MIT](LICENSE) del progetto.
