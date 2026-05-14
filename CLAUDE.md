# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app
streamlit run app.py

# Install dependencies (after activating venv)
pip install -r requirements.txt

# Activate virtual environment (Windows)
venv\Scripts\activate
```

There are no automated tests or linting configuration in this project.

## Architecture

This is a **Streamlit multi-page audit application** for the Diputación de Sevilla's RCF (Registro Contable de Facturas) system. The app audits electronic invoice compliance according to Spanish public administration law (Guía IGAE).

### Data flow

1. User uploads 4 Excel files via the sidebar in `app.py`
2. `utils/data_loader.py` normalizes column names (flexible mapping handles inconsistent Excel headers) and stores DataFrames in `st.session_state['datos']`
3. Each page reads from `st.session_state['datos']` independently — pages are stateless except for writing analysis results back to `st.session_state['analisis']` for use by the report generator

### Key files

- `app.py` — Entry point: file upload, data loading, session initialization
- `config/settings.py` — All audit parameters: thresholds (`importe_minimo_obligatorio = 3000`), exercise year, entity name, HAP validation codes, corporate colors
- `utils/data_loader.py` — Column normalization (`MAPEO_COLUMNAS`), helper functions (`obtener_facturas_papel_sospechosas`, `es_persona_juridica`, `excluir_facturas_borradas`)
- `utils/validaciones.py` — HAP/1650/2015 validation logic using `validaciones.csv` as code→rule mapping
- `pages/7_Generar_Informe.py` — Reads `st.session_state['analisis']` populated by other pages to generate Word/PDF reports

### Pages (audit sections)

| File | Section | Purpose |
|------|---------|---------|
| `1_Dashboard.py` | — | KPIs and overview charts |
| `2_Facturas_Papel.py` | V.1 | Paper invoices exceeding 3.000€ BI (Ley 25/2013 compliance) |
| `3_Anotacion_RCF.py` | V.2 | Time between FACe registration and RCF annotation |
| `4_Validaciones.py` | V.3 | HAP/1650/2015 content validations via rejection codes |
| `5_Tramitacion.py` | V.4 | Invoice state transitions and cancellations |
| `6_Obligaciones.py` | V.5 | Late payment and invoices pending >3 months |
| `7_Generar_Informe.py` | — | Word/PDF report generation |

### Critical business rules

**"BORRADA" invoices**: Excluded from most analyses (Dashboard, Papel, Tiempos, Morosidad) but **included** in Validaciones (section V.3) — the RCF system marks failed HAP validations as BORRADA, so excluding them would hide the errors.

**Paper invoice detection** (`es_papel`): Invoices without a FACe identifier. Suspicious ones are PJ (Persona Jurídica) + `base_imponible > 3000€` + not BORRADA.

**Persona Jurídica detection** (`es_persona_juridica` in `data_loader.py`): Checks NIF prefix (A, B, C, D, E, F, G, H, J, U, V) as fallback when `tipo_persona != 'J'`.

**Validations** use `validaciones.csv` (root directory) mapping first 8 chars of `motivo_rechazo` → HAP code (e.g. `RCF06001` → `6a`). If this file is missing, validations return empty results silently.

**Column normalization**: Excel column names are inconsistent across data sources. `data_loader.py` maps variants (`'BI'`, `'IMP. BASE IMPONIBLE'`, `'base_imponible'` → `base_imponible`). When adding new data processing, always work with normalized column names.

**Audit exercise**: Controlled globally via `CONFIGURACION['ejercicio_auditado']` in `config/settings.py`. Data is filtered to 2025 during load — do not hardcode year logic in pages.
