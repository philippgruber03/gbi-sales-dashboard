# Changelog - Global Bike Inc. (GBI) Sales Dashboard

All notable changes and architectural updates to this project are automatically documented in this file in chronological order.

## [2026-10-21 15:43] - spec.md
- **Change Summary**: Created and finalized complete technical specification `spec.md` following the `/grill-me` alignment.
- **Rationale**: Formulates the architectural, design (SAP Fiori Horizon + IBCS), data schema, and functional view requirements for all subsequent implementation steps.
- **Status**: Completed / Approved.

## [2026-10-21 15:43] - requirements.txt
- **Change Summary**: Created `requirements.txt` containing free, open-source dependencies (Streamlit, Pandas, OpenPyXL, Plotly, SQLAlchemy).
- **Rationale**: Ensure reproducible environment setup and strictly enforce 100% free open-source tooling constraint.
- **Status**: Completed.

## [2026-10-21 15:43] - styles/fiori_horizon.css
- **Change Summary**: Created custom CSS stylesheet implementing SAP Fiori Horizon design guidelines.
- **Rationale**: Styles top Shellbar header (`#354A5F`), primary buttons/tabs (`#0A6ED1`), neutral canvas (`#F5F7FA`), KPI cards, and IBCS threshold badges.
- **Status**: Completed.

## [2026-10-21 15:44] - generate_test_data.py
- **Change Summary**: Created standalone test data generator script producing realistic GBI data across 5 years (2015-2019).
- **Rationale**: Generates `gbi_test_data.xlsx` (max 200 records per sheet) and seeds local SQLite database `gbi_sales.db` via SQLAlchemy. Pre-calibrates product margins around the critical 46% threshold and seasonal bike patterns for 2019.
- **Status**: Completed.

## [2026-10-21 15:45] - data_engine.py
- **Change Summary**: Implemented modular `GBIDataEngine` pipeline supporting Excel (`.xlsx`) and SQLite via SQLAlchemy.
- **Rationale**: Provides schema validation, contribution margin derivations, and specialized transformation methods for all 4 views (Customer drill-downs, Product 46% margin evaluations & Top/Bottom rankings, 2019 bike monthly seasonality, and 5-year dynamic pivot matrix).
- **Status**: Completed.

## [2026-10-21 15:46] - ibcs_charts.py
- **Change Summary**: Created Plotly visualization module strictly adhering to IBCS SUCCESS and SAP Fiori Horizon guidelines.
- **Rationale**: Prohibits pie/donut and 3D charts. Implements horizontal time-axes, horizontal bar charts for structural rankings, 46% critical margin threshold reference line with semantic red/green alert coloring, IBCS Small Multiples with synchronized Y-axis scaling for 2019 bike seasonality, and 5-year dynamic multi-dimension charts.
- **Status**: Completed.

## [2026-10-21 15:47] - app.py
- **Change Summary**: Created complete main Streamlit application featuring SAP Fiori Horizon Shellbar, sidebar pipeline controls, and all 4 interactive views.
- **Rationale**: Integrates data loading from Excel/SQLite, multi-level hierarchy drill-downs (View 1), 46% margin evaluations & Top/Bottom rankings (View 2), IBCS Small Multiples bike revenue seasonality for 2019 (View 3), and 5-year dynamic pivot matrix with CSV/Excel exports (View 4).
- **Status**: Completed.

## [2026-10-21 15:47] - data_engine.py
- **Change Summary**: Converted dynamic pivot matrix column headers explicitly to string format (`str(c)`).
- **Rationale**: Eliminates Pandas mixed-type column name warning when appending `"Total"` summary column to integer year headers.
- **Status**: Completed.

## [2026-10-21 15:48] - test_dashboard.py
- **Change Summary**: Created automated unit and integration test suite covering data generator, pipeline, 4 views, 46% margin thresholds, and strict IBCS compliance checks (no pie/donut or 3D).
- **Rationale**: Ensure verifiable test coverage, automated regression prevention, and strict validation of all functional requirements.
- **Status**: Completed.

## [2026-10-21 15:48] - README.md & run_dashboard.bat
- **Change Summary**: Added comprehensive project README documentation and single-click Windows batch launcher `run_dashboard.bat`.
- **Rationale**: User-friendly onboarding, architecture description, and quick-launch functionality.
- **Status**: Completed / Ready for Production.

## [2026-10-21 16:07] - app.py, ibcs_charts.py, data_engine.py, styles/fiori_horizon.css, test_dashboard.py
- **Change Summary**:
  - Entfernung sämtlicher fester Jahreszahlen in den Tab-Reitern und View-Überschriften aller 4 Views.
  - Vollständige Lokalisierung auf Deutsch (keine englischen Begriffe mehr in Shellbar, Filtern, KPI-Kacheln, Diagrammen, Tooltips und Exporten).
  - View 1 (Kundenanalyse): Flexibler Jahresfilter (einzelnes Jahr wie 2017, Spanne 2017–2018 oder 2017–2019) statt fest verdrahteter 3 Jahre; klare Fiori-Filterboxen zur Trennung von Diagramm 1 (Zeitverlauf) und Diagramm 2 (Kundenvergleich); kategorische Zeitachse (`type=category`) zur strikten Vermeidung von Dezimaljahren (kein 2017,5) inkl. Umschaltung zwischen ganzen Jahren und detailliertem Monatsverlauf.
  - View 2 (Produktanalyse & Deckungsbeitrag): Bereinigung der 46 %-Referenzlinie (Entfernung der Bezeichnung "IBCS" im Benchmark-Label; jetzt "Referenzlinie (46 %)"); Vergrößerung des Abstands zwischen Gesamttitel und Subplot-Titeln im Ranking-Diagramm gegen Überlappung.
  - View 3 (Fahrrad-Umsatzanalyse): Entfernung der "Executive Summary"-Box; Ergänzung interaktiver Filter für Geschäftsjahre und darunterliegender Monate.
  - View 4 (Dynamische Analyse): Direkte Datenbeschriftung der Werte ÜBER den Balken (`textposition="outside"`); flexibler Filter für Geschäftsjahre (2015–2017, 2015–2019 oder Einzeljahre); klar hervorgehobene Filterbox für Produktkategorien (Air Hawk, Fly Deluxe, Offroad, Touring, Zubehör) mit vergrößertem Abstand.
  - Aktualisierung der automatisierten Test-Suite (7 von 7 Tests erfolgreich).
- **Rationale**: Direkte Umsetzung des Benutzerfeedbacks zur UX-Klarheit, Filterflexibilität, IBCS-Reinheit und optischen Abständen.
- **Status**: Abgenommen & Vollständig funktionsfähig.

## [2026-10-21 16:19] - app.py, ibcs_charts.py
- **Change Summary**:
  - Sämtliche Informationskästen / Banner-Boxen über allen Views restlos entfernt (keine künstlichen Info-Header wie "Globaler Zeitraum-Filter...", "Filter & Steuerung...", etc.).
  - Die Zuordnung der Filter zu den jeweiligen Visualisierungen erfolgt nun intuitiv und sauber ausschließlich über die räumliche Positionierung direkt über dem jeweiligen Diagramm.
  - Der Filter für die Geschäftsjahre (`Geschäftsjahre:`) wurde links in die Sidebar unter die globalen Filter verschoben und wirkt global auf alle Views.
  - Sämtliche Bezeichnungen wie "Diagramm 1:", "Diagramm 2:", "Diagramm 3:" überall im Dashboard entfernt.
  - Der Zeitverlauf bei Auswahl von ganzen Jahren wurde explizit auf **"Gesamtumsatz"** umbenannt.
  - In View 2 (Produktanalyse) wurde der Text "Gestrichelte Linie" entfernt; stattdessen ist die 46 %-Referenzlinie im Diagramm selbst deutlich sichtbar gestrichelt (`line_width=2.5`, `line_dash="dash"`).
- **Rationale**: Direkte Umsetzung des Benutzerfeedbacks zur Reduktion von visueller Redundanz und Maximierung des Data-Ink-Ratios im SAP Fiori Horizon Stil.
- **Status**: Erfolgreich getestet & abgenommen.

## [2026-10-21 16:40] - .gitignore
- **Change Summary**: Created `.gitignore` excluding Python bytecode cache (`__pycache__/`, `*.pyc`) and IDE metadata.
- **Rationale**: Prevents committing compiled binary cache to the public GitHub repository.
- **Status**: Completed.
