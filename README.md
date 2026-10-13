# Electrolyte Emergency Agent

### [Open the Live Application →](https://abusuraihsakhri.github.io/electrolyte-emergency-agent/)

Python-based electrolyte calculation prototypes, a generic rule-based audit interface, and a lightweight browser research calculator.

> **Clinical limitation:** Research and teaching only. **Not validated for diagnosis, dosing, prescribing, infusion pump control, or emergency patient management.** No algorithm here can replace an ECG, serial blood testing, clinical assessment, or local hospital protocols. Do not enter real patient identifiers.

## What is implemented

- `electrolyte_guard.py`: sodium deficit arithmetic, experimental hyponatremia correction estimates, potassium categories, and example calcium, magnesium, phosphorus, fluid and medication calculations. **Dose outputs have not undergone independent clinical validation; do not use them for treatment.**
- `electrolyte_emergency_agent/`: a separate generic CSV/CLI/API audit engine using primary/secondary metrics and user-specified flags. Its thresholds are **not electrolyte diagnostic cutoffs**.
- `agents/`: another generic worker/supervisor prototype with an in-memory HMAC-linked audit record, a regex-based identifier check, and a mock response adapter. It is not a deployable clinical decision-support system.
- `enrichment.py`: illustrative scoring components, **not** live smart-pump, ICU registry, predictive model, or dialysis integrations.
- `web/index.html`: static educational UI that downloads Pyodide and runs the repository's Python calculator **locally in the browser**. The UI currently exposes *sodium deficit arithmetic* and *non-diagnostic potassium categories*; no dose-regimen interface is provided.

## Browser application

The static app is published through GitHub Pages. CI verifies that the published HTML and Python source are retrievable over HTTPS. For local use:

```bash
python -m http.server 8001
# Open http://localhost:8001/web/index.html
```

It requires a modern browser with WebAssembly and access to the version-pinned Pyodide distribution hosted on jsDelivr. Calculations execute in the local Python WebAssembly runtime; the app does not upload entered numbers. The Python runtime and its standard-library files are downloaded from a third-party CDN. No identifiers should be submitted. Do not rely on the browser as an offline-first app or an emergency-care tool.

## Installation and CLI

Python 3.10+:

```bash
python -m pip install -e ".[api,test]"
python -m pytest -q
electrolyte-guard hyponatremia --na 120 --desired-na 125 --weight 70
electrolyte-emergency-engine audit --primary 14 --secondary 5 --status NORMAL
electrolyte-emergency-engine batch -i sample.csv -o results.csv
```

The `electrolyte-guard` command exposes unvalidated illustrative treatment routines. The `electrolyte-emergency-engine` command takes generic synthetic metrics and is separate from the electrolyte calculator. Its API can be run locally:

```bash
electrolyte-emergency-engine serve --host 127.0.0.1 --port 8000
```

The server provides `GET /health`, `POST /api/audit`, and `POST /api/chat`. The additional `agents.api` prototype has separate health, metrics, audit, chat, and audit log routes. **Neither server implements user authentication or a verified PHI-handling workflow; never expose it as a public clinical service.**

## Container

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
# http://127.0.0.1:8000/health
```

The container binds to localhost by default. Configure a new random secret for each deployment and store it securely outside source control. The HMAC audit trail is **in-memory**, is lost on restart, and is not an immutable compliance-grade audit system. Regex-based identifier detection is incomplete and cannot guarantee de-identification.

## Tests and verification

```bash
python -m pytest -q
python -m compileall -q agents electrolyte_emergency_agent electrolyte_guard.py enrichment.py
```

GitHub Actions tests Python 3.10–3.12, JavaScript syntax, package installation, finite-number input validation, correction-time boundaries, CSV parsing, and audit-signature tampering. After successful tests on `master`, the workflow builds a static Pages artifact from `web/index.html` and `electrolyte_guard.py`.

## Clinical and implementation caveats

A sodium deficit formula is a simplified mass-balance estimate, **not** a validated 3% saline infusion rate. The time-scaled sodium change ceiling in the prototype illustrates published correction *limits*, not treatment *targets*; ODS risk cannot be inferred from those values alone. Potassium concentration does not reliably predict ECG findings. Medication and fluid recommendations in older prototype functions may be outdated or inappropriate in individual patients and require independent clinical review.

For background see [European hyponatremia clinical practice guideline (2014)](https://doi.org/10.1530/EJE-13-1020) and [UK Kidney Association hyperkalaemia guideline](https://www.ukkidney.org/health-professionals/guidelines/treatment-acute-hyperkalaemia-adults-0). These references do **not** imply that this software implements or has been validated against those guidelines.

## Technology and license

Python standard library for the electrolyte calculator; optional FastAPI/Pydantic/Uvicorn for APIs; pytest for tests; HTML/CSS/JavaScript and Pyodide for the browser UI; Docker and GitHub Actions for packaging/deployment. Compatible with modern Chromium, Firefox, and Safari browsers that support WebAssembly. Licensed under [MIT](LICENSE).
