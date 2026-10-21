"""
app.py - Global Bike Inc. (GBI) Sales Dashboard
Enterprise Business Intelligence Dashboard nach SAP Fiori Horizon & IBCS SUCCESS Standards.
100 % freier Open-Source-Stack: Streamlit, Pandas, OpenPyXL, Plotly, SQLAlchemy, SQLite.
Rein deutsche Benutzeroberfläche ohne störende Informationskästen; intuitive Filterzuordnung durch Positionierung.
"""

import os
import io
import streamlit as st
import pandas as pd

from data_engine import GBIDataEngine
from ibcs_charts import (
    create_customer_hierarchy_chart,
    create_sales_org_breakdown_chart,
    create_time_drilldown_chart,
    create_margin_threshold_chart,
    create_top_bottom_ranking_chart,
    create_bike_revenue_small_multiples,
    create_dynamic_analysis_chart
)
from generate_test_data import export_data

# Page Setup
st.set_page_config(
    page_title="GBI Sales Dashboard | SAP Fiori Horizon",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Styles
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
css_path = os.path.join(CURRENT_DIR, "styles", "fiori_horizon.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Data Engine
engine = GBIDataEngine(base_dir=CURRENT_DIR)

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("### ⚙️ Datenquelle & Pipeline")
    data_source_mode = st.radio(
        "Aktive Datenquelle:",
        options=["Standard-Testdaten (Excel)", "Lokale SQLite-Datenbank (SQLAlchemy)", "Eigene Excel-Datei hochladen (.xlsx)"],
        index=0
    )

    df_raw = None
    source_label = "Unbekannt"

    try:
        if data_source_mode == "Standard-Testdaten (Excel)":
            if not os.path.exists(engine.excel_default_path):
                export_data(CURRENT_DIR)
            df_raw = engine.load_from_excel(engine.excel_default_path)
            source_label = "gbi_test_data.xlsx (Excel)"

        elif data_source_mode == "Lokale SQLite-Datenbank (SQLAlchemy)":
            if not os.path.exists(engine.sqlite_default_path):
                export_data(CURRENT_DIR)
            df_raw = engine.load_from_sqlite(engine.sqlite_default_path)
            source_label = "gbi_sales.db (SQLite/SQLAlchemy)"

        elif data_source_mode == "Eigene Excel-Datei hochladen (.xlsx)":
            uploaded_file = st.file_uploader("Eigene Excel-Datei auswählen (.xlsx):", type=["xlsx"])
            if uploaded_file is not None:
                df_raw = engine.load_from_excel(uploaded_file)
                source_label = f"Upload: {uploaded_file.name}"
            else:
                st.info("Keine Datei ausgewählt. Fallback auf Standard-Testdaten aktiv.")
                if not os.path.exists(engine.excel_default_path):
                    export_data(CURRENT_DIR)
                df_raw = engine.load_from_excel(engine.excel_default_path)
                source_label = "Fallback: gbi_test_data.xlsx"

    except Exception as err:
        st.error(f"Fehler beim Datenimport: {err}")
        st.stop()

    if st.button("🔄 Testdaten neu generieren", use_container_width=True):
        export_data(CURRENT_DIR)
        st.success("Testdaten erfolgreich neu generiert!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Globale Filter")

    # 1. Global Filter: Geschäftsjahre (links in der Sidebar platziert)
    available_years = sorted(df_raw["Year"].unique().tolist())
    selected_years = st.multiselect(
        "Geschäftsjahre:",
        options=available_years,
        default=available_years,
        help="Filtert den gesamten Datenbestand des Dashboards nach den ausgewählten Jahren."
    )

    # 2. Global Filter: Sales Organization
    available_orgs = sorted(df_raw["Sales_Org"].unique().tolist())
    selected_orgs = st.multiselect("Verkaufsorganisation (Sales Org):", options=available_orgs, default=available_orgs)

    # 3. Global Filter: Division
    available_divs = sorted(df_raw["Division"].unique().tolist())
    div_labels = {"BI": "BI – Fahrräder (Bicycles)", "AS": "AS – Zubehör (Accessories)"}
    selected_divs = st.multiselect(
        "Sparte (Division):",
        options=available_divs,
        default=available_divs,
        format_func=lambda x: div_labels.get(x, x)
    )

    # Apply Global Filters
    filtered_df = df_raw[
        (df_raw["Year"].isin(selected_years)) &
        (df_raw["Sales_Org"].isin(selected_orgs)) &
        (df_raw["Division"].isin(selected_divs))
    ].copy()

    if len(filtered_df) == 0:
        st.warning("Keine Daten für die gewählten Filter vorhanden. Bitte Filter in der Sidebar anpassen.")
        st.stop()

# ----------------- SAP FIORI HORIZON SHELLBAR -----------------
st.markdown(
    """
    <div class="fiori-shellbar">
        <div class="fiori-shellbar-brand">
            <span class="fiori-shellbar-logo">🚲 GLOBAL BIKE INC.</span>
            <span class="fiori-shellbar-subtitle">Vertriebs-Reporting & Management Dashboard</span>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            <span class="fiori-shellbar-badge">SAP Fiori Horizon</span>
            <span class="fiori-shellbar-badge" style="background:rgba(46,125,50,0.3); color:#E8F5E9;">IBCS-konform</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------- TABS / NAVIGATION (OHNE JAHRESANGABEN) -----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "👥 Kundenanalyse",
    "🚲 Produktanalyse & Deckungsbeitrag",
    "📅 Fahrrad-Umsatzanalyse",
    "📊 Dynamische Analyse"
])

# ==============================================================================
# VIEW 1: KUNDENANALYSE
# ==============================================================================
with tab1:
    st.markdown('<div class="view-section-title">👥 Kundenanalyse</div>', unsafe_allow_html=True)
    v1_df = filtered_df

    # Fiori Metric Tiles
    tot_rev = v1_df["Revenue_USD"].sum()
    tot_qty = v1_df["Sales_Quantity"].sum()
    tot_cogm = v1_df["COGM_USD"].sum()
    tot_margin = tot_rev - tot_cogm
    margin_pct = (tot_margin / tot_rev * 100) if tot_rev > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="fiori-kpi-tile">
                <div class="fiori-kpi-title">Bruttoumsatz</div>
                <div class="fiori-kpi-value">${tot_rev:,.0f}</div>
                <div class="fiori-kpi-sub">Gesamtumsatz in USD</div>
            </div>
            """, unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div class="fiori-kpi-tile">
                <div class="fiori-kpi-title">Absatzmenge</div>
                <div class="fiori-kpi-value">{int(tot_qty):,} Stk</div>
                <div class="fiori-kpi-sub">Verkaufte Einheiten</div>
            </div>
            """, unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div class="fiori-kpi-tile">
                <div class="fiori-kpi-title">Herstellkosten (COGM)</div>
                <div class="fiori-kpi-value">${tot_cogm:,.0f}</div>
                <div class="fiori-kpi-sub">Herstellungskosten in USD</div>
            </div>
            """, unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            f"""
            <div class="fiori-kpi-tile">
                <div class="fiori-kpi-title">Deckungsbeitrag</div>
                <div class="fiori-kpi-value">${tot_margin:,.0f}</div>
                <div class="fiori-kpi-sub">Marge: <span class="{'fiori-kpi-positive' if margin_pct >= 46 else 'fiori-kpi-negative'}">{margin_pct:.1f} %</span></div>
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown('<div class="view-spacer"></div>', unsafe_allow_html=True)

    # Spaltenaufteilung: Filter sind rein durch ihre Positionierung dem jeweiligen Diagramm zugeordnet
    col_vis1, col_vis2 = st.columns(2)

    with col_vis1:
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            time_granularity = st.radio(
                "Zeitachse formatieren als:",
                options=["Ganze Jahre", "Detaillierter Monatsverlauf"],
                index=0,
                key="v1_time_granularity"
            )
        with sub_c2:
            metric_time = st.selectbox(
                "Kennzahl für Zeitverlauf:",
                options=["Revenue_USD", "Sales_Quantity", "COGM_USD"],
                format_func=lambda x: {"Revenue_USD": "Bruttoumsatz ($)", "Sales_Quantity": "Absatzmenge (Stk)", "COGM_USD": "Herstellkosten ($)"}[x],
                key="v1_metric_time"
            )

        # Ganze Jahre wird explizit "Gesamtumsatz" genannt
        time_chart_title = "Gesamtumsatz" if time_granularity == "Ganze Jahre" else "Monatlicher Zeitverlauf"
        fig_time = create_time_drilldown_chart(
            v1_df,
            time_col="Year",
            measure_col=metric_time,
            title=time_chart_title,
            detailed_mode=(time_granularity == "Detaillierter Monatsverlauf")
        )
        st.plotly_chart(fig_time, use_container_width=True)

    with col_vis2:
        sub_k1, sub_k2 = st.columns(2)
        with sub_k1:
            cust_level = st.selectbox(
                "Kunden-Hierarchie aufbohren:",
                options=["Country", "Customer_Group", "Customer"],
                format_func=lambda x: {"Country": "Land", "Customer_Group": "Kundengruppe", "Customer": "Einzelkunde"}[x],
                key="v1_cust_level"
            )
        with sub_k2:
            metric_cust = st.selectbox(
                "Kennzahl für Kundenvergleich:",
                options=["Revenue_USD", "Sales_Quantity", "COGM_USD"],
                format_func=lambda x: {"Revenue_USD": "Bruttoumsatz ($)", "Sales_Quantity": "Absatzmenge (Stk)", "COGM_USD": "Herstellkosten ($)"}[x],
                key="v1_metric_cust"
            )

        fig_cust = create_customer_hierarchy_chart(
            v1_df,
            group_col=cust_level,
            measure_col=metric_cust,
            title=f"Kunden-Strukturvergleich nach {cust_level}"
        )
        st.plotly_chart(fig_cust, use_container_width=True)

    st.markdown('<div class="view-spacer"></div>', unsafe_allow_html=True)

    # Strukturvergleich Sales Organization
    st.markdown(
        """
        <div class="fiori-card-header" style="margin-top:1.5rem;">
            <span>🏢 Verteilung nach Verkaufsorganisation (DN00, DS00, DB00, DS01)</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    fig_org = create_sales_org_breakdown_chart(
        v1_df,
        measure_col=metric_time,
        title=f"Verteilung nach Verkaufsorganisation"
    )
    st.plotly_chart(fig_org, use_container_width=True)


# ==============================================================================
# VIEW 2: PRODUKTANALYSE & DECKUNGSBEITRAG
# ==============================================================================
with tab2:
    st.markdown('<div class="view-section-title">🚲 Produktanalyse & Deckungsbeitrag</div>', unsafe_allow_html=True)
    prod_agg, top_5_bikes, bottom_5_bikes = engine.get_product_view_data(filtered_df)

    if len(prod_agg) == 0:
        st.info("Keine Produktdaten für die gewählten Filter vorhanden.")
    else:
        # Übersichtskarten
        above_count = len(prod_agg[prod_agg["Margin_Pct"] >= 46.0])
        below_count = len(prod_agg[prod_agg["Margin_Pct"] < 46.0])
        best_prod = prod_agg.iloc[0]
        worst_prod = prod_agg.iloc[-1]

        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.markdown(
                f"""
                <div class="fiori-kpi-tile">
                    <div class="fiori-kpi-title">Schwellenwert-Status (&ge; 46 %)</div>
                    <div class="fiori-kpi-value"><span class="fiori-kpi-positive">{above_count}</span> / {len(prod_agg)}</div>
                    <div class="fiori-kpi-sub">Produkte über Schwellenwert</div>
                </div>
                """, unsafe_allow_html=True
            )
        with kpi_c2:
            st.markdown(
                f"""
                <div class="fiori-kpi-tile">
                    <div class="fiori-kpi-title">Kritische Produkte (&lt; 46 %)</div>
                    <div class="fiori-kpi-value"><span class="fiori-kpi-negative">{below_count}</span> Produkte</div>
                    <div class="fiori-kpi-sub">Unter dem Schwellenwert</div>
                </div>
                """, unsafe_allow_html=True
            )
        with kpi_c3:
            st.markdown(
                f"""
                <div class="fiori-kpi-tile">
                    <div class="fiori-kpi-title">Höchste Marge</div>
                    <div class="fiori-kpi-value">{best_prod['Margin_Pct']:.1f} %</div>
                    <div class="fiori-kpi-sub">{best_prod['Product']}</div>
                </div>
                """, unsafe_allow_html=True
            )
        with kpi_c4:
            st.markdown(
                f"""
                <div class="fiori-kpi-tile">
                    <div class="fiori-kpi-title">Niedrigste Marge</div>
                    <div class="fiori-kpi-value">{worst_prod['Margin_Pct']:.1f} %</div>
                    <div class="fiori-kpi-sub">{worst_prod['Product']}</div>
                </div>
                """, unsafe_allow_html=True
            )

        st.markdown('<div class="view-spacer"></div>', unsafe_allow_html=True)

        # 1. Deckungsbeitrags-Diagramm: Linie ist direkt gestrichelt ohne störende Textbox
        fig_margin = create_margin_threshold_chart(prod_agg, threshold=46.0)
        st.plotly_chart(fig_margin, use_container_width=True)

        st.markdown('<div class="view-spacer"></div>', unsafe_allow_html=True)

        # 2. Ranking Top 5 / Flop 5 mit ausreichendem Abstand
        st.markdown(
            """
            <div class="fiori-card-header" style="margin-top:1.5rem; margin-bottom:1rem;">
                <span>🏆 Fahrrad-Absatzmengen: Top 5 & Flop 5 nach verkauften Einheiten</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        if len(top_5_bikes) > 0:
            fig_ranking = create_top_bottom_ranking_chart(top_5_bikes, bottom_5_bikes)
            st.plotly_chart(fig_ranking, use_container_width=True)
        else:
            st.info("Keine Fahrräder (Sparte BI) für das Ranking verfügbar.")

        # Detail-Tabelle
        with st.expander("🔍 Produkttabelle im Detail einblenden"):
            display_cols = ["Product", "Product_Category", "Division", "Revenue_USD", "COGM_USD", "Margin_USD", "Margin_Pct", "Sales_Quantity"]
            col_rename = {
                "Product": "Produkt",
                "Product_Category": "Kategorie",
                "Division": "Sparte",
                "Revenue_USD": "Bruttoumsatz",
                "COGM_USD": "Herstellkosten",
                "Margin_USD": "Deckungsbeitrag ($)",
                "Margin_Pct": "Deckungsbeitrag (%)",
                "Sales_Quantity": "Absatzmenge"
            }
            renamed_df = prod_agg[display_cols].rename(columns=col_rename)
            st.dataframe(
                renamed_df.style.format({
                    "Bruttoumsatz": "${:,.2f}",
                    "Herstellkosten": "${:,.2f}",
                    "Deckungsbeitrag ($)": "${:,.2f}",
                    "Deckungsbeitrag (%)": "{:.2f} %",
                    "Absatzmenge": "{:,} Stk"
                }),
                use_container_width=True
            )


# ==============================================================================
# VIEW 3: FAHRRAD-UMSATZANALYSE (SMALL MULTIPLES)
# ==============================================================================
with tab3:
    st.markdown('<div class="view-section-title">📅 Fahrrad-Umsatzanalyse</div>', unsafe_allow_html=True)

    all_years_v3 = sorted(filtered_df[filtered_df["Division"] == "BI"]["Year"].unique().tolist())
    latest_year = all_years_v3[-1] if len(all_years_v3) > 0 else 2019

    # Filter direkt über dem Chart platziert (ohne Informationskasten)
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        selected_years_v3 = st.multiselect(
            "Geschäftsjahr(e) für Saisonalitätsverlauf:",
            options=all_years_v3,
            default=[latest_year],
            key="v3_years_select"
        )

    with f_col2:
        month_labels = {
            1: "01 - Januar", 2: "02 - Februar", 3: "03 - März", 4: "04 - April",
            5: "05 - Mai", 6: "06 - Juni", 7: "07 - Juli", 8: "08 - August",
            9: "09 - September", 10: "10 - Oktober", 11: "11 - November", 12: "12 - Dezember"
        }
        selected_months_v3 = st.multiselect(
            "Monate eingrenzen:",
            options=list(range(1, 13)),
            default=list(range(1, 13)),
            format_func=lambda m: month_labels[m],
            key="v3_months_select"
        )

    if not selected_years_v3 or not selected_months_v3:
        st.warning("Bitte mindestens ein Geschäftsjahr und einen Monat auswählen.")
    else:
        monthly_seasonal = engine.get_bike_revenue_seasonal(
            filtered_df,
            selected_years=selected_years_v3,
            selected_months=selected_months_v3
        )

        year_str = ", ".join(str(y) for y in sorted(selected_years_v3))
        fig_multiples = create_bike_revenue_small_multiples(monthly_seasonal, subtitle=f"Geschäftsjahr: {year_str}")
        st.plotly_chart(fig_multiples, use_container_width=True)

        # Monatliche Matrix als Tabelle
        with st.expander("📋 Monatliche Umsatzmatrix nach Kategorie einblenden"):
            pivot_seasonal = pd.pivot_table(
                monthly_seasonal,
                values="Revenue_USD",
                index="Month_Name",
                columns="Product_Category",
                aggfunc="sum",
                fill_value=0
            )
            month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            pivot_seasonal = pivot_seasonal.reindex([m for m in month_order if m in pivot_seasonal.index])
            pivot_seasonal["Gesamt"] = pivot_seasonal.sum(axis=1)

            st.dataframe(
                pivot_seasonal.style.format("${:,.2f}"),
                use_container_width=True
            )


# ==============================================================================
# VIEW 4: DYNAMISCHE ANALYSE
# ==============================================================================
with tab4:
    st.markdown('<div class="view-section-title">📊 Dynamische Analyse</div>', unsafe_allow_html=True)
    st.markdown("Interaktive Pivot-Matrix und Zeitreihenauswertung: Kennzahlen frei gegen Dimensionen auf der Zeitachse auswerten.")

    st.markdown('<div class="view-spacer"></div>', unsafe_allow_html=True)

    all_years_v4 = sorted(filtered_df["Year"].unique().tolist())
    all_categories = sorted(filtered_df["Product_Category"].unique().tolist())

    # Filter-Steuerelemente direkt über dem Chart (ohne Informationsbox)
    col_ctrl1, col_ctrl2 = st.columns(2)
    with col_ctrl1:
        measure_opts = {
            "Revenue_USD": "Bruttoumsatz ($)",
            "Sales_Quantity": "Absatzmenge (Stk)",
            "COGM_USD": "Herstellkosten (COGM) ($)",
            "Discount_USD": "Rabatt / Skonto ($)"
        }
        selected_measure = st.selectbox(
            "Kennzahl (Measure) wählen:",
            options=list(measure_opts.keys()),
            format_func=lambda x: measure_opts[x],
            key="v4_measure_select"
        )

    with col_ctrl2:
        dim_opts = {
            "Product_Category": "Produktkategorie",
            "Country": "Land",
            "Sales_Org": "Verkaufsorganisation (Sales Org)",
            "Division": "Sparte (Division)"
        }
        selected_dim = st.selectbox(
            "Dimension wählen:",
            options=list(dim_opts.keys()),
            format_func=lambda x: dim_opts[x],
            key="v4_dim_select"
        )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_years_v4 = st.multiselect(
            "Geschäftsjahre filtern (z. B. 2015–2017, 2015–2019 oder Einzeljahre):",
            options=all_years_v4,
            default=all_years_v4,
            key="v4_years_select"
        )

    with col_f2:
        selected_cats_v4 = st.multiselect(
            "Produktkategorien filtern:",
            options=all_categories,
            default=all_categories,
            key="v4_cats_select"
        )

    st.markdown('<div class="view-spacer"></div>', unsafe_allow_html=True)

    if not selected_years_v4 or not selected_cats_v4:
        st.warning("Bitte mindestens ein Geschäftsjahr und eine Produktkategorie auswählen.")
    else:
        # Dynamische Aggregation berechnen
        pivot_matrix, dynamic_grouped = engine.get_dynamic_analysis(
            filtered_df,
            measure_col=selected_measure,
            dimension_col=selected_dim,
            selected_years=selected_years_v4,
            selected_categories=selected_cats_v4
        )

        if len(dynamic_grouped) == 0:
            st.info("Keine Daten für die gewählte Filterkombination vorhanden.")
        else:
            # 1. Dynamisches Diagramm mit WERTEN DIREKT ÜBER DEN BALKEN
            fig_dyn = create_dynamic_analysis_chart(
                dynamic_grouped,
                measure_name=measure_opts[selected_measure],
                dimension_name=dim_opts[selected_dim]
            )
            st.plotly_chart(fig_dyn, use_container_width=True)

            st.markdown('<div class="view-spacer"></div>', unsafe_allow_html=True)

            # 2. Interaktive Pivot-Matrix mit Gesamtsumme
            st.markdown(f"##### 📊 Dynamische Matrix: {dim_opts[selected_dim]} × Geschäftsjahre")
            
            if selected_measure in ["Revenue_USD", "COGM_USD", "Discount_USD"]:
                formatted_pvt = pivot_matrix.style.format("${:,.2f}")
            else:
                formatted_pvt = pivot_matrix.style.format("{:,}")

            st.dataframe(formatted_pvt, use_container_width=True)

            # Export-Buttons (CSV und Excel)
            exp_c1, exp_c2, _ = st.columns([1, 1, 2])
            with exp_c1:
                csv_data = pivot_matrix.to_csv().encode("utf-8")
                st.download_button(
                    label="📥 Als CSV exportieren",
                    data=csv_data,
                    file_name=f"dynamische_analyse_{selected_measure}_{selected_dim}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with exp_c2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    pivot_matrix.to_excel(writer, sheet_name="Dynamische_Analyse")
                st.download_button(
                    label="📥 Als Excel exportieren",
                    data=buffer.getvalue(),
                    file_name=f"dynamische_analyse_{selected_measure}_{selected_dim}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

# ----------------- FOOTER -----------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; color:#94A3B8; font-size:0.75rem; padding: 12px 0;">
        Global Bike Inc. (GBI) Sales Dashboard | Entwickelt nach <b>SAP Fiori Horizon</b> & <b>IBCS SUCCESS Standards</b> | 100 % freier Open-Source-Stack
    </div>
    """,
    unsafe_allow_html=True
)
