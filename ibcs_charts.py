"""
ibcs_charts.py - IBCS & SAP Fiori Horizon Compliant Chart Generation
Strikte Einhaltung der IBCS SUCCESS-Regeln:
- STRENGES VERBOT von Pie-/Donut- und 3D-Diagrammen.
- Horizontale Zeitachsen für Zeitreihen (diskrete Kategorien, keine Dezimaljahre wie 2017,5).
- Horizontale Balkendiagramme für Struktur- und Rankingvergleiche.
- Direkte Datenbeschriftungen an/über den Balken (hohe Datendichte).
- Signalfarben (Grün #2E7D32 / Rot #C83232) ausschließlich für Schwellenwert- und Abweichungsanalysen.
- Ausreichend Weißraum, Padding und Abstände zwischen Titeln, Subplots und Achsen.
- Rein deutsche Beschriftung aller Diagrammelemente.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# SAP Fiori Horizon & IBCS Farbdefinitionen
COLOR_PRIMARY_BLUE = "#0A6ED1"
COLOR_SLATE_DARK = "#354A5F"
COLOR_BAR_NEUTRAL = "#475569"
COLOR_BAR_LIGHT = "#94A3B8"
COLOR_ALERT_GREEN = "#2E7D32"  # Ziel erreicht / Positiv
COLOR_ALERT_RED = "#C83232"    # Unter Schwellenwert / Kritisch
COLOR_BENCHMARK_LINE = "#1E293B"
COLOR_GRID = "#E2E8F0"

def get_base_ibcs_layout(title=""):
    """Liefert das Standard-IBCS-Layout mit Fiori-Schriftart, dezenten Gitternetzlinien und großzügigen Abständen."""
    return go.Layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=14, color=COLOR_SLATE_DARK, family="'72', -apple-system, Segoe UI, Arial, sans-serif"),
            x=0.0,
            xanchor="left",
            y=0.98,
            yanchor="top",
            pad=dict(b=14, t=6)
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=60, r=50, t=80, b=55),
        font=dict(family="'72', -apple-system, Segoe UI, Arial, sans-serif", size=11, color="#334155"),
        xaxis=dict(
            showgrid=False,
            zeroline=True,
            zerolinecolor="#94A3B8",
            zerolinewidth=1,
            showline=True,
            linecolor="#CBD5E1",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLOR_GRID,
            gridwidth=1,
            zeroline=False,
            showline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
    )

# ----------------- VIEW 1: KUNDENANALYSE -----------------
def create_customer_hierarchy_chart(df, group_col="Customer", measure_col="Revenue_USD", title="Strukturvergleich nach Kunde"):
    """Horizontales IBCS-Balkendiagramm für den Kunden-Strukturvergleich."""
    agg = df.groupby(group_col)[measure_col].sum().sort_values(ascending=True).reset_index()
    
    if "Revenue" in measure_col or "COGM" in measure_col or "Discount" in measure_col:
        text_labels = [f"${v:,.0f}" for v in agg[measure_col]]
    else:
        text_labels = [f"{int(v):,} Stk" for v in agg[measure_col]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg[group_col],
        x=agg[measure_col],
        orientation="h",
        marker=dict(color=COLOR_SLATE_DARK),
        text=text_labels,
        textposition="outside",
        cliponaxis=False,
        name=measure_col,
        hovertemplate="<b>%{y}</b><br>Wert: %{text}<extra></extra>"
    ))

    layout = get_base_ibcs_layout(title)
    layout.yaxis.showgrid = False
    layout.xaxis.showgrid = True
    layout.xaxis.gridcolor = COLOR_GRID
    layout.margin.l = 170
    fig.update_layout(layout)
    return fig

def create_sales_org_breakdown_chart(df, measure_col="Revenue_USD", title="Verteilung nach Verkaufsorganisation"):
    """IBCS-Säulendiagramm zum Vergleich der Verkaufsorganisationen."""
    agg = df.groupby("Sales_Org")[measure_col].sum().reset_index().sort_values(by=measure_col, ascending=False)
    
    if "Revenue" in measure_col or "COGM" in measure_col or "Discount" in measure_col:
        text_labels = [f"${v:,.0f}" for v in agg[measure_col]]
    else:
        text_labels = [f"{int(v):,} Stk" for v in agg[measure_col]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["Sales_Org"],
        y=agg[measure_col],
        marker=dict(color=COLOR_PRIMARY_BLUE),
        text=text_labels,
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>Verkaufsorganisation %{x}</b><br>Wert: %{text}<extra></extra>"
    ))

    layout = get_base_ibcs_layout(title)
    layout.xaxis.title = "Verkaufsorganisation (Sales Org)"
    fig.update_layout(layout)
    return fig

def create_time_drilldown_chart(df, time_col="Year", measure_col="Revenue_USD", title="Zeitlicher Verlauf", detailed_mode=False):
    """
    Horizontale IBCS-Zeitachse.
    WICHTIG: Die Zeitachse ist strikt kategorisch ('type=category') formatiert.
    Dadurch werden niemals Dezimaljahre wie 2017,5 dargestellt!
    """
    if detailed_mode:
        # Sort chronologically by Year and Month
        agg = df.groupby(["Year", "Month", "Month_Name"])[measure_col].sum().reset_index()
        agg = agg.sort_values(by=["Year", "Month"])
        agg["Time_Label"] = agg.apply(lambda r: f"{r['Month_Name']} {int(r['Year'])}", axis=1)
        x_vals = agg["Time_Label"].tolist()
        y_vals = agg[measure_col].tolist()
    else:
        agg = df.groupby(time_col)[measure_col].sum().reset_index().sort_values(by=time_col)
        # Ensure strict string conversion so Plotly renders discrete categories
        x_vals = [str(x) for x in agg[time_col]]
        y_vals = agg[measure_col].tolist()
    
    if "Revenue" in measure_col or "COGM" in measure_col or "Discount" in measure_col:
        text_labels = [f"${v/1000:,.1f}k" if v >= 1000 else f"${v:,.0f}" for v in y_vals]
    else:
        text_labels = [f"{int(v):,} Stk" for v in y_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_vals,
        y=y_vals,
        marker=dict(color=COLOR_BAR_NEUTRAL),
        text=text_labels,
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>Zeit: %{x}</b><br>Wert: %{text}<extra></extra>"
    ))

    layout = get_base_ibcs_layout(title)
    # Categorical x-axis guarantees no interpolation of decimals like 2017.5
    layout.xaxis.type = "category"
    layout.xaxis.title = "Zeitachse"
    fig.update_layout(layout)
    return fig

# ----------------- VIEW 2: PRODUKTANALYSE & DECKUNGSBEITRAG -----------------
def create_margin_threshold_chart(prod_agg, threshold=46.0):
    """
    IBCS-Deckungsbeitragsdiagramm mit 46 % Referenzlinie.
    WICHTIG: Die Beschriftung lautet 'Referenzlinie (46 %)' (keine Nennung von 'IBCS').
    Grün für >= 46 %, Rot für < 46 %.
    """
    df_sorted = prod_agg.sort_values(by="Margin_Pct", ascending=True).copy()
    
    colors = [COLOR_ALERT_GREEN if m >= threshold else COLOR_ALERT_RED for m in df_sorted["Margin_Pct"]]
    labels = [f"{m:.1f}%" for m in df_sorted["Margin_Pct"]]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_sorted["Product"],
        x=df_sorted["Margin_Pct"],
        orientation="h",
        marker=dict(color=colors),
        text=labels,
        textposition="outside",
        cliponaxis=False,
        name="Deckungsbeitrag %",
        hovertemplate="<b>%{y}</b><br>Deckungsbeitrag: %{x:.2f}%<br>Sparte: %{customdata}<extra></extra>",
        customdata=df_sorted["Division"]
    ))

    # Vertikale Referenzlinie bei 46 % (deutlich sichtbar gestrichelt direkt im Chart)
    fig.add_vline(
        x=threshold,
        line_width=2.5,
        line_dash="dash",
        line_color=COLOR_BENCHMARK_LINE,
        annotation_text=f"Referenzlinie ({threshold:.0f} %)",
        annotation_position="top",
        annotation_font=dict(size=11, color=COLOR_BENCHMARK_LINE, family="'72', Arial")
    )

    layout = get_base_ibcs_layout("Deckungsbeitrag je Produkt (Schwellenwert: 46 %)")
    layout.xaxis.title = "Deckungsbeitrag (%)"
    layout.yaxis.showgrid = False
    layout.xaxis.showgrid = True
    layout.xaxis.gridcolor = COLOR_GRID
    layout.margin.l = 175
    layout.margin.t = 85
    layout.margin.b = 55
    layout.xaxis.range = [0, max(df_sorted["Margin_Pct"].max() * 1.18, 65)]
    fig.update_layout(layout)
    return fig

def create_top_bottom_ranking_chart(top_5, bottom_5):
    """
    IBCS-Ranking der Top 5 und Flop 5 Fahrräder nach Absatzmenge.
    Mit großzügigem Abstand zwischen Gesamttitel, Subplot-Titeln und Datenbalken.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "<b>Top 5 Fahrräder (Höchste Absatzmenge)</b>",
            "<b>Flop 5 Fahrräder (Geringste Absatzmenge)</b>"
        ),
        shared_yaxes=False,
        horizontal_spacing=0.25
    )

    # Top 5 Trace
    top_sorted = top_5.sort_values(by="Sales_Quantity", ascending=True)
    fig.add_trace(go.Bar(
        y=top_sorted["Product"],
        x=top_sorted["Sales_Quantity"],
        orientation="h",
        marker=dict(color=COLOR_PRIMARY_BLUE),
        text=[f"{int(q):,} Stk" for q in top_sorted["Sales_Quantity"]],
        textposition="outside",
        cliponaxis=False,
        name="Top 5 Einheiten",
        hovertemplate="<b>%{y}</b><br>Absatzmenge: %{x:,} Stk<extra></extra>"
    ), row=1, col=1)

    # Bottom 5 Trace
    bottom_sorted = bottom_5.sort_values(by="Sales_Quantity", ascending=True)
    fig.add_trace(go.Bar(
        y=bottom_sorted["Product"],
        x=bottom_sorted["Sales_Quantity"],
        orientation="h",
        marker=dict(color=COLOR_SLATE_DARK),
        text=[f"{int(q):,} Stk" for q in bottom_sorted["Sales_Quantity"]],
        textposition="outside",
        cliponaxis=False,
        name="Flop 5 Einheiten",
        hovertemplate="<b>%{y}</b><br>Absatzmenge: %{x:,} Stk<extra></extra>"
    ), row=1, col=2)

    layout = get_base_ibcs_layout("Fahrrad-Absatzmengen im Vergleich (Verkaufte Einheiten)")
    layout.showlegend = False
    layout.margin.l = 160
    layout.margin.r = 70
    layout.margin.t = 100  # Großzügiger Abstand, damit Gesamttitel nicht mit Subplot-Titeln kollidiert
    layout.margin.b = 55
    fig.update_layout(layout)
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_GRID, title_text="Absatz (Stück)")
    fig.update_yaxes(showgrid=False)
    return fig

# ----------------- VIEW 3: FAHRRAD-UMSATZANALYSE (SMALL MULTIPLES) -----------------
def create_bike_revenue_small_multiples(monthly_data, subtitle=""):
    """
    IBCS Small Multiples: 4 synchron skalierte monatliche Sub-Charts je Fahrrad-Kategorie.
    Verhindert unlesbare Kurvenüberlagerungen ('Spaghetti-Charts').
    """
    categories = ["Air Hawk", "Fly Deluxe", "Offroad", "Touring"]
    
    # Globales Maximum zur einheitlichen Y-Achsen-Skalierung
    max_rev = monthly_data["Revenue_USD"].max()
    global_max_rev = max(max_rev * 1.25, 1000)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"<b>Kategorie: {cat}</b>" for cat in categories],
        vertical_spacing=0.22,
        horizontal_spacing=0.10
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for cat, (r, c) in zip(categories, positions):
        cat_df = monthly_data[monthly_data["Product_Category"] == cat].sort_values(by="Month")
        
        fig.add_trace(
            go.Bar(
                x=cat_df["Month_Name"],
                y=cat_df["Revenue_USD"],
                marker=dict(color=COLOR_SLATE_DARK),
                name=cat,
                text=[f"${v/1000:,.0f}k" if v >= 1000 else (f"${v:,.0f}" if v > 0 else "") for v in cat_df["Revenue_USD"]],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{x}</b><br>Bruttoumsatz: $%{y:,.0f}<extra></extra>"
            ),
            row=r, col=c
        )

    full_title = "Monatlicher Fahrrad-Umsatzverlauf nach Kategorie (Small Multiples)"
    if subtitle:
        full_title += f" – {subtitle}"

    layout = get_base_ibcs_layout(full_title)
    layout.showlegend = False
    layout.height = 680
    layout.margin.t = 95
    layout.margin.b = 55
    fig.update_layout(layout)
    
    # Synchronisierte Y-Achsen für alle 4 Kategorien nach IBCS
    for i in range(1, 5):
        fig.update_yaxes(range=[0, global_max_rev], showgrid=True, gridcolor=COLOR_GRID, title_text="Umsatz ($)")
        fig.update_xaxes(showgrid=False)

    return fig

# ----------------- VIEW 4: DYNAMISCHE ANALYSE -----------------
def create_dynamic_analysis_chart(grouped_df, measure_name="Bruttoumsatz ($)", dimension_name="Produktkategorie"):
    """
    Dynamisches Zeitreihendiagramm mit direkter Beschriftung der Werte ÜBER den Balken.
    """
    dim_col = grouped_df.columns[1]
    measure_col = grouped_df.columns[2]

    fig = go.Figure()
    palette = [COLOR_PRIMARY_BLUE, COLOR_SLATE_DARK, "#059669", "#D97706", "#7C3AED", "#DB2777"]

    unique_dims = grouped_df[dim_col].unique()
    for idx, dim_val in enumerate(unique_dims):
        subset = grouped_df[grouped_df[dim_col] == dim_val].sort_values(by="Year")
        color = palette[idx % len(palette)]
        
        # Format text labels directly above the bars
        if "USD" in measure_col or "$" in measure_name or "Umsatz" in measure_name or "Herstellkosten" in measure_name or "Rabatt" in measure_name:
            val_labels = [f"${v/1000:,.1f}k" if v >= 1000 else f"${v:,.0f}" for v in subset[measure_col]]
        else:
            val_labels = [f"{int(v):,}" for v in subset[measure_col]]

        fig.add_trace(go.Bar(
            x=[str(int(y)) if isinstance(y, (int, float)) else str(y) for y in subset["Year"]],
            y=subset[measure_col],
            name=str(dim_val),
            marker=dict(color=color),
            text=val_labels,
            textposition="outside",
            cliponaxis=False,
            hovertemplate=f"<b>{dim_val}</b> (%{{x}})<br>{measure_name}: %{{text}}<extra></extra>"
        ))

    layout = get_base_ibcs_layout(f"Dynamische Analyse: {measure_name} nach {dimension_name}")
    layout.barmode = "group"
    layout.xaxis.title = "Geschäftsjahr"
    layout.xaxis.type = "category"  # Verhindert 2017,5
    layout.yaxis.title = measure_name
    layout.margin.t = 95
    layout.margin.b = 60
    fig.update_layout(layout)
    return fig
