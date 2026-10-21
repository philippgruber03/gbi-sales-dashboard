# Technische & Funktionale Spezifikation: Global Bike Inc. (GBI) Sales Dashboard

## 1. Management Summary & Zielsetzung
Das GBI Sales Dashboard ist eine interaktive Business-Intelligence-Anwendung für das Management und den Vertrieb des SAP-Lernunternehmens **Global Bike Inc. (GBI)**.
- **Design-Leitfaden**: SAP Fiori Horizon Theme (Shellbar `#354A5F`, Primärakzent `#0A6ED1`, neutraler Canvas `#F5F7FA`, weiße Cards `#FFFFFF`, KPI-Kacheln).
- **IBCS SUCCESS Standards**:
  - **STRENGES VERBOT** von Pie-/Donut- und 3D-Diagrammen.
  - Horizontale Zeitachsen für Zeitreihen (kategorische Formatierung, keine Dezimaljahre).
  - Horizontale Balkendiagramme für Struktur- und Rankingvergleiche.
  - Direkte Wertebeschriftung an den Datenpunkten (hohe Datendichte).
  - Signalfarben (Grün `#2E7D32` / Rot `#C83232`) ausschließlich für Schwellenwert-Verletzungen.
- **100 % freier Open-Source-Stack**: Python 3.x, Streamlit, Pandas, OpenPyXL, Plotly, SQLAlchemy, SQLite.
- **Vollständige deutsche Lokalisierung**: Keine englischen Fachbegriffe im User Interface.
- **Reduktives Fiori-Layout**: Keine störenden Informations- oder Bannerboxen. Filterzuordnungen ergeben sich intuitiv und rein durch die räumliche Positionierung direkt über der jeweiligen Visualisierung.

---

## 2. Architektur & Dateistruktur

```
Dashboard/
├── app.py                  # Hauptanwendung (Fiori Shellbar, Tab-Navigation, globale Sidebar-Filter, 4 Views)
├── spec.md                 # Vollständige funktionale und technische Spezifikation
├── CHANGELOG.md            # Automatisches Protokoll sämtlicher Änderungen und Iterationen
├── requirements.txt        # Freie Open-Source-Bibliotheken
├── generate_test_data.py   # Testdatengenerator (gbi_test_data.xlsx & SQLite gbi_sales.db)
├── data_engine.py          # Modulare Daten-Pipeline (GBIDataEngine) mit Validierung & Filterung
├── ibcs_charts.py          # IBCS- & Fiori-konforme Diagramm-Generierung mit Plotly
├── test_dashboard.py       # Automatisierte Testsuite (Unit- & Integrationstests)
├── run_dashboard.bat       # 1-Klick-Starter für Windows
├── README.md               # Projektdokumentation und Bedienungsanleitung
├── gbi_test_data.xlsx      # Testdaten (Sales_Orders, Customers, Products, max. 200 Zeilen/Sheet)
├── gbi_sales.db            # Lokale SQLite-Datenbank via SQLAlchemy
└── styles/
    └── fiori_horizon.css   # SAP Fiori Horizon CSS (Shellbar, Filterboxen, KPI-Kacheln)
```

---

## 3. Datenmodell & Berechnungen

### 3.1 Entität `Sales_Orders`
- `Sales_Order_ID`, `Order_Date`, `Year`, `Quarter`, `Month`, `Month_Name`
- `Country` (US, DE), `Sales_Org` (DN00, DS00, DB00, DS01), `Division` (BI, AS)
- `Customer_Group` (Gewerblich, Privat, Bildung), `Customer`
- `Product_Category` (Air Hawk, Fly Deluxe, Offroad, Touring, Zubehör), `Product`
- `Sales_Quantity`, `Revenue_USD`, `COGM_USD`, `Discount_USD`

### 3.2 Kennzahlen & Formeln
- **Bruttoumsatz**: `Revenue_USD`
- **Herstellkosten**: `COGM_USD`
- **Deckungsbeitrag ($)**: `Revenue_USD - COGM_USD`
- **Deckungsbeitrag (%)**:
  $$\text{Deckungsbeitrag \%} = \frac{\text{Revenue\_USD} - \text{COGM\_USD}}{\text{Revenue\_USD}} \times 100$$
- **Schwellenwert / Referenzlinie**: 46,0 %
  - $\ge 46,0\%$: Ziel erreicht (IBCS-Grün: `#2E7D32`)
  - $< 46,0\%$: Kritisch / Unter Schwellenwert (IBCS-Rot: `#C83232`)

---

## 4. Detaillierte Spezifikation der 4 Views

### Globale Filter (Sidebar links)
- **Geschäftsjahre**: Multiselect-Filter zur Auswahl einzelner Jahre oder Jahresspannen (wirkt global auf alle 4 Views).
- **Verkaufsorganisation**: Filterung nach `DN00`, `DS00`, `DB00`, `DS01`.
- **Sparte (Division)**: Filterung nach `BI – Fahrräder` und `AS – Zubehör`.

### View 1: Kundenanalyse
- **KPI-Kacheln**: Bruttoumsatz, Absatzmenge, Herstellkosten (COGM), Deckungsbeitrag.
- **Intuitive Positionierung der Steuerungen**:
  - Linke Spalte: Steuerelemente für Zeitachse (Ganze Jahre vs. Detaillierter Monatsverlauf) und Kennzahlenauswahl direkt über dem Zeitdiagramm.
  - Bei Auswahl von „Ganze Jahre“ lautet die Diagrammüberschrift prägnant **„Gesamtumsatz“**.
  - Rechte Spalte: Steuerelemente für Kundenhierarchie (Land, Kundengruppe, Einzelkunde) und Kennzahlenauswahl direkt über dem Kunden-Balkendiagramm.
  - Keine vorangestellten Kennzeichnungen wie „Diagramm 1:“ oder „Diagramm 2:“.
- **Verkaufsorganisation**: Strukturverteilung nach Sales Org (DN00, DS00, DB00, DS01).

### View 2: Produktanalyse & Deckungsbeitrag
- **46 % Deckungsbeitrags-Schwellenwert**:
  - Horizontales Balkendiagramm mit deutlich gestrichelter vertikaler Linie (`line_dash="dash"`, `line_width=2.5`) und direkter Beschriftung **„Referenzlinie (46 %)“**.
  - Keine künstlichen Textkästen („Gestrichelte Linie...“).
  - Farbliche Differenzierung: Grün ($\ge 46\%$), Rot ($< 46\%$).
- **Top 5 & Flop 5 Ranking**:
  - Horizontales Balkendiagramm der Fahrräder nach Absatzmenge mit exakter Mengenausweisung am Balken und großzügigem Weißraum.

### View 3: Fahrrad-Umsatzanalyse
- **Filter**: Auswahl des Geschäftsjahres (oder mehrerer Jahre) und darunterliegende Monatswahl direkt über der Visualisierung platziert (ohne Informationsbox).
- **IBCS Small Multiples**: 4 synchron skalierte Sub-Charts für die Fahrradkategorien (*Air Hawk, Fly Deluxe, Offroad, Touring*) zur Analyse der Frühjahrs-/Sommer-Saisonalität.

### View 4: Dynamische Analyse
- **Filterung**: Wählbare Kennzahlen, Dimensionen, Geschäftsjahre und Produktkategorien direkt über dem Diagramm platziert (ohne Informationsbox).
- **Direkte Wertebeschriftung**: Bruttoumsatz und Kennzahlenwerte werden direkt **über den Balken** (`textposition="outside"`) angezeigt.
- **Kombinierte Darstellung**: Dynamisches IBCS-Säulendiagramm und interaktive Pivot-Tabelle mit Gesamtsummenzeile und 1-Klick-Export nach **Excel** und **CSV**.
