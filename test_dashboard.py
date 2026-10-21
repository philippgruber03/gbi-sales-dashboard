"""
test_dashboard.py - Umfassende Test-Suite für das GBI Sales Dashboard
Überprüft Datenimport, dynamische Filter, IBCS-Konformität (keine Pie/Donut/3D),
Referenzlinien-Beschriftung (ohne IBCS-Präfix), direkte Balkenbeschriftungen und Zeitachsen.
"""

import os
import unittest
import pandas as pd
from data_engine import GBIDataEngine
from generate_test_data import export_data
from ibcs_charts import (
    create_customer_hierarchy_chart,
    create_sales_org_breakdown_chart,
    create_time_drilldown_chart,
    create_margin_threshold_chart,
    create_top_bottom_ranking_chart,
    create_bike_revenue_small_multiples,
    create_dynamic_analysis_chart
)

class TestGBIDashboard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.abspath(__file__))
        cls.excel_path, cls.db_path = export_data(cls.base_dir)
        cls.engine = GBIDataEngine(base_dir=cls.base_dir)

    def test_01_test_data_files_exist_and_bounded(self):
        """Überprüft Existenz der Dateien und Obergrenze von 200 Zeilen je Sheet."""
        self.assertTrue(os.path.exists(self.excel_path))
        self.assertTrue(os.path.exists(self.db_path))

        xl = pd.ExcelFile(self.excel_path)
        self.assertIn("Sales_Orders", xl.sheet_names)
        self.assertIn("Customers", xl.sheet_names)
        self.assertIn("Products", xl.sheet_names)

        df_orders = xl.parse("Sales_Orders")
        self.assertLessEqual(len(df_orders), 200)
        self.assertGreater(len(df_orders), 100)

    def test_02_data_engine_loading(self):
        """Testet den Import über Excel und SQLite via SQLAlchemy."""
        df_excel = self.engine.load_from_excel(self.excel_path)
        self.assertIn("Margin_USD", df_excel.columns)
        self.assertIn("Margin_Pct", df_excel.columns)
        self.assertIn("Threshold_46_Met", df_excel.columns)

        df_sql = self.engine.load_from_sqlite(self.db_path)
        self.assertEqual(len(df_excel), len(df_sql))

    def test_03_view_1_flexible_year_filter(self):
        """Testet flexiblen Jahresfilter in View 1 (z. B. einzelnes Jahr 2017 oder Bereich 2017-2019)."""
        df = self.engine.load_from_excel(self.excel_path)
        
        # Test 1: Einzelnes Jahr 2017
        v1_single = self.engine.get_customer_view_data(df, selected_years=[2017])
        self.assertEqual(set(v1_single["Year"].unique()), {2017})

        # Test 2: Spanne 2017 bis 2018
        v1_range = self.engine.get_customer_view_data(df, selected_years=[2017, 2018])
        self.assertEqual(set(v1_range["Year"].unique()), {2017, 2018})

        # Chart-Tests
        fig_cust = create_customer_hierarchy_chart(v1_range, group_col="Customer", measure_col="Revenue_USD")
        self.assertIsNotNone(fig_cust)

        # Zeitachsen-Test: stellt sicher, dass type="category" gesetzt ist (keine 2017,5)
        fig_time = create_time_drilldown_chart(v1_range, time_col="Year", measure_col="Revenue_USD", detailed_mode=False)
        self.assertEqual(fig_time.layout.xaxis.type, "category")

        fig_time_detailed = create_time_drilldown_chart(v1_range, time_col="Year", measure_col="Revenue_USD", detailed_mode=True)
        self.assertEqual(fig_time_detailed.layout.xaxis.type, "category")

    def test_04_view_2_margin_benchmark_annotation(self):
        """Überprüft, dass bei der 46%-Referenzlinie NICHT das Wort 'IBCS' steht."""
        df = self.engine.load_from_excel(self.excel_path)
        prod_agg, top_5, bottom_5 = self.engine.get_product_view_data(df)

        fig_margin = create_margin_threshold_chart(prod_agg, threshold=46.0)
        
        # Überprüfe Annotations / Shape Text
        found_ref = False
        for annot in fig_margin.layout.annotations:
            text = annot.text
            self.assertNotIn("IBCS", text, "Annotation darf nicht das Wort 'IBCS' enthalten!")
            if "Referenzlinie" in text:
                found_ref = True
        self.assertTrue(found_ref, "Referenzlinie-Annotation wurde nicht gefunden!")

        # Top/Flop Chart
        fig_ranking = create_top_bottom_ranking_chart(top_5, bottom_5)
        self.assertIsNotNone(fig_ranking)
        self.assertGreater(fig_ranking.layout.margin.t, 70, "Oberer Rand muss genügend Abstand haben!")

    def test_05_view_3_seasonal_multiples_with_year_month_filter(self):
        """Testet dynamische Filterung nach Jahren und Monaten in View 3."""
        df = self.engine.load_from_excel(self.excel_path)
        
        # Nur 2018 und Monate 3, 4, 5
        monthly = self.engine.get_bike_revenue_seasonal(df, selected_years=[2018], selected_months=[3, 4, 5])
        self.assertEqual(len(monthly), 3 * 4) # 3 Monate * 4 Kategorien

        fig_sm = create_bike_revenue_small_multiples(monthly, subtitle="Test")
        self.assertIsNotNone(fig_sm)

    def test_06_view_4_dynamic_analysis_and_bar_labels(self):
        """Testet View 4: Werte direkt über den Balken und flexible Filter."""
        df = self.engine.load_from_excel(self.excel_path)
        pvt, grouped = self.engine.get_dynamic_analysis(
            df,
            measure_col="Revenue_USD",
            dimension_col="Product_Category",
            selected_years=[2016, 2017, 2018],
            selected_categories=["Air Hawk", "Fly Deluxe"]
        )

        self.assertIn("Gesamt", pvt.columns)
        self.assertGreater(len(grouped), 0)

        fig_dyn = create_dynamic_analysis_chart(grouped, measure_name="Bruttoumsatz ($)", dimension_name="Produktkategorie")
        # Überprüfe, dass textposition="outside" gesetzt ist
        for trace in fig_dyn.data:
            self.assertEqual(trace.textposition, "outside", "Werte müssen direkt über den Balken stehen (outside)!")

    def test_07_ibcs_strict_compliance(self):
        """Verifiziert das strikte Verbot von Pie-, Donut- und 3D-Charts."""
        df = self.engine.load_from_excel(self.excel_path)
        v1_df = self.engine.get_customer_view_data(df)
        prod_agg, top_5, bottom_5 = self.engine.get_product_view_data(df)
        monthly = self.engine.get_bike_revenue_seasonal(df)
        _, grouped = self.engine.get_dynamic_analysis(df)

        figs = [
            create_customer_hierarchy_chart(v1_df),
            create_sales_org_breakdown_chart(v1_df),
            create_time_drilldown_chart(v1_df),
            create_margin_threshold_chart(prod_agg),
            create_top_bottom_ranking_chart(top_5, bottom_5),
            create_bike_revenue_small_multiples(monthly),
            create_dynamic_analysis_chart(grouped)
        ]

        for idx, fig in enumerate(figs):
            for trace in fig.data:
                trace_type = trace.type
                self.assertNotIn(trace_type, ["pie", "donut", "surface", "mesh3d", "scatter3d"],
                                 f"Unzulässiger Diagrammtyp '{trace_type}' in Abbildung {idx} gefunden!")

if __name__ == "__main__":
    unittest.main()
