"""
data_engine.py - Modulare Daten-Pipeline für das GBI Sales Dashboard
Ermöglicht den flexiblen Datenimport aus Excel (.xlsx) und SQLite via SQLAlchemy,
Schema-Validierung, Berechnung von Kennzahlen (Deckungsbeitrag) und Aggregationen für alle Views.
"""

import os
import pandas as pd
from sqlalchemy import create_engine

# Erwartete Spalten für GBI-Vertriebsdaten
EXPECTED_COLUMNS = [
    "Sales_Order_ID", "Order_Date", "Year", "Quarter", "Month", "Month_Name",
    "Country", "Sales_Org", "Division", "Customer_Group", "Customer",
    "Product_Category", "Product", "Sales_Quantity", "Revenue_USD",
    "COGM_USD", "Discount_USD"
]

class GBIDataEngine:
    """Modulare Daten-Engine zum Laden, Transformieren und Aggregieren der GBI-Vertriebsdaten."""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self.excel_default_path = os.path.join(base_dir, "gbi_test_data.xlsx")
        self.sqlite_default_path = os.path.join(base_dir, "gbi_sales.db")

    def load_from_excel(self, file_or_path=None, sheet_name="Sales_Orders"):
        """Lädt Daten aus einer Excel-Datei oder einem Streamlit Upload-Buffer."""
        target = file_or_path if file_or_path is not None else self.excel_default_path
        try:
            xl = pd.ExcelFile(target)
            selected_sheet = sheet_name if sheet_name in xl.sheet_names else xl.sheet_names[0]
            df = xl.parse(selected_sheet)
            return self._enrich_and_validate(df)
        except Exception as e:
            raise RuntimeError(f"Fehler beim Laden der Excel-Datei ({target}): {e}")

    def load_from_sqlite(self, db_path=None, table_name="sales_orders"):
        """Lädt Daten aus der lokalen SQLite-Datenbank via SQLAlchemy."""
        target_db = db_path if db_path is not None else self.sqlite_default_path
        try:
            engine = create_engine(f"sqlite:///{target_db}")
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, engine)
            return self._enrich_and_validate(df)
        except Exception as e:
            raise RuntimeError(f"Fehler bei SQLite-Abfrage an {target_db}: {e}")

    def _enrich_and_validate(self, df):
        """Validiert das Schema und berechnet abgeleitete betriebswirtschaftliche Kennzahlen."""
        clean_df = df.copy()

        # Spaltennamen bereinigen
        clean_df.columns = [c.strip() for c in clean_df.columns]

        # Numerische Typkonvertierung
        numeric_cols = ["Year", "Month", "Sales_Quantity", "Revenue_USD", "COGM_USD", "Discount_USD"]
        for col in numeric_cols:
            if col in clean_df.columns:
                clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce").fillna(0)

        if "Year" in clean_df.columns:
            clean_df["Year"] = clean_df["Year"].astype(int)
        if "Month" in clean_df.columns:
            clean_df["Month"] = clean_df["Month"].astype(int)

        # Deckungsbeitrag (Margin USD) und Deckungsbeitrag in %
        if "Revenue_USD" in clean_df.columns and "COGM_USD" in clean_df.columns:
            clean_df["Margin_USD"] = clean_df["Revenue_USD"] - clean_df["COGM_USD"]
            clean_df["Margin_Pct"] = (
                clean_df.apply(
                    lambda r: (r["Margin_USD"] / r["Revenue_USD"] * 100.0) if r["Revenue_USD"] > 0 else 0.0,
                    axis=1
                )
            ).round(2)
        else:
            clean_df["Margin_USD"] = 0.0
            clean_df["Margin_Pct"] = 0.0

        # Schwellenwert-Status (>= 46.0 %)
        clean_df["Threshold_46_Met"] = clean_df["Margin_Pct"] >= 46.0

        # Chronologische Sortierung
        if "Order_Date" in clean_df.columns:
            clean_df["Order_Date"] = pd.to_datetime(clean_df["Order_Date"], errors="coerce")
            clean_df = clean_df.sort_values(by=["Year", "Month", "Order_Date"])

        return clean_df

    # ---------------- VIEW 1: KUNDENANALYSE ----------------
    def get_customer_view_data(self, df, selected_years=None):
        """Filtert flexibel nach den ausgewählten Jahren (z. B. einzelnes Jahr oder 2017-2019)."""
        if selected_years is not None and len(selected_years) > 0:
            return df[df["Year"].isin(selected_years)].copy()
        # Fallback: letzte 3 verfügbare Jahre
        all_years = sorted(df["Year"].unique().tolist())
        fallback_years = all_years[-3:] if len(all_years) >= 3 else all_years
        return df[df["Year"].isin(fallback_years)].copy()

    # ---------------- VIEW 2: PRODUKTANALYSE & MARGEN ----------------
    def get_product_view_data(self, df):
        """Aggregiert Produktdaten und ermittelt Top/Flop 5 Fahrräder sowie 46 % Deckungsbeitrags-Kennzahlen."""
        prod_agg = df.groupby(["Product", "Product_Category", "Division"]).agg(
            Revenue_USD=("Revenue_USD", "sum"),
            Sales_Quantity=("Sales_Quantity", "sum"),
            COGM_USD=("COGM_USD", "sum"),
        ).reset_index()

        prod_agg["Margin_USD"] = prod_agg["Revenue_USD"] - prod_agg["COGM_USD"]
        prod_agg["Margin_Pct"] = (
            prod_agg.apply(
                lambda r: (r["Margin_USD"] / r["Revenue_USD"] * 100.0) if r["Revenue_USD"] > 0 else 0.0,
                axis=1
            )
        ).round(2)
        prod_agg["Above_Threshold"] = prod_agg["Margin_Pct"] >= 46.0
        prod_agg = prod_agg.sort_values(by="Margin_Pct", ascending=False)

        # Ausschließlich Fahrräder (Division BI) für das Top/Flop-Ranking
        bikes_df = prod_agg[prod_agg["Division"] == "BI"].sort_values(by="Sales_Quantity", ascending=False)
        top_5_bikes = bikes_df.head(5).copy()
        bottom_5_bikes = bikes_df.tail(5).sort_values(by="Sales_Quantity", ascending=True).copy()

        return prod_agg, top_5_bikes, bottom_5_bikes

    # ---------------- VIEW 3: FAHRRAD-UMSATZANALYSE (SAISONALITÄT) ----------------
    def get_bike_revenue_seasonal(self, df, selected_years=None, selected_months=None):
        """
        Ermittelt monatliche Fahrrad-Umsätze (Division BI) nach Produktkategorie.
        Erlaubt die flexible Filterung nach Jahren und Monaten.
        """
        v3_df = df[df["Division"] == "BI"].copy()

        if selected_years is not None and len(selected_years) > 0:
            v3_df = v3_df[v3_df["Year"].isin(selected_years)]
        else:
            # Standardmäßig das aktuellste Jahr
            max_year = df["Year"].max()
            v3_df = v3_df[v3_df["Year"] == max_year]

        if selected_months is not None and len(selected_months) > 0:
            v3_df = v3_df[v3_df["Month"].isin(selected_months)]

        # Monatliche Aggregation nach Produktkategorie
        monthly_cat = v3_df.groupby(["Month", "Month_Name", "Product_Category"]).agg(
            Revenue_USD=("Revenue_USD", "sum"),
            Sales_Quantity=("Sales_Quantity", "sum")
        ).reset_index()

        # Vollständiges Raster zur Sicherstellung konsistenter IBCS Small Multiples
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        categories = ["Air Hawk", "Fly Deluxe", "Offroad", "Touring"]
        
        target_months = selected_months if (selected_months is not None and len(selected_months) > 0) else list(range(1, 13))

        full_grid = []
        for m in target_months:
            for cat in categories:
                full_grid.append({"Month": m, "Month_Name": month_names[m - 1], "Product_Category": cat})
        grid_df = pd.DataFrame(full_grid)

        merged = pd.merge(grid_df, monthly_cat, on=["Month", "Month_Name", "Product_Category"], how="left").fillna(0)
        merged = merged.sort_values(by=["Product_Category", "Month"])
        return merged

    # Kompatibilitätsmethode für frühere Aufrufe
    def get_bike_revenue_2019(self, df, year=2019):
        return self.get_bike_revenue_seasonal(df, selected_years=[year])

    # ---------------- VIEW 4: DYNAMISCHE ANALYSE ----------------
    def get_dynamic_analysis(self, df, measure_col="Revenue_USD", dimension_col="Product_Category", selected_years=None, selected_categories=None):
        """
        Erstellt dynamische Kreuztabelle (Pivot-Matrix) und gruppierte Zeitreihendaten.
        Unterstützt Filterung nach Jahren und Produktkategorien.
        """
        filtered_sub = df.copy()

        if selected_years is not None and len(selected_years) > 0:
            filtered_sub = filtered_sub[filtered_sub["Year"].isin(selected_years)]

        if selected_categories is not None and len(selected_categories) > 0:
            filtered_sub = filtered_sub[filtered_sub["Product_Category"].isin(selected_categories)]

        if len(filtered_sub) == 0:
            return pd.DataFrame(), pd.DataFrame()

        # Pivot-Tabelle
        pvt = pd.pivot_table(
            filtered_sub,
            values=measure_col,
            index=dimension_col,
            columns="Year",
            aggfunc="sum",
            fill_value=0
        )
        # Spaltenbezeichnungen explizit als String formatieren
        pvt.columns = [str(c) for c in pvt.columns]
        
        # Zeilensumme (Total) berechnen
        pvt["Gesamt"] = pvt.sum(axis=1)
        pvt = pvt.sort_values(by="Gesamt", ascending=False)

        # Gruppierte Daten für das Plotly-Diagramm
        df_grouped = filtered_sub.groupby(["Year", dimension_col])[measure_col].sum().reset_index()
        return pvt, df_grouped
