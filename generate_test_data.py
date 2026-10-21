"""
generate_test_data.py - Test Data Generator for Global Bike Inc. (GBI) Sales Dashboard
Generates realistic GBI sales dataset conforming to SAP GBI curriculum standards,
exports to 'gbi_test_data.xlsx' (max 200 rows per sheet) and seeds 'gbi_sales.db' via SQLAlchemy.
"""

import os
import random
import datetime
import pandas as pd
from sqlalchemy import create_engine

# Set fixed random seed for reproducible benchmark test data
random.seed(42)

GBI_CUSTOMERS = [
    {"customer_id": "C-101", "customer": "Silicon Valley Bikes", "customer_group": "Commercial", "country": "US", "city": "Palo Alto"},
    {"customer_id": "C-102", "customer": "Beantown Bikes", "customer_group": "Commercial", "country": "US", "city": "Boston"},
    {"customer_id": "C-103", "customer": "Big Apple Cyclery", "customer_group": "Consumer", "country": "US", "city": "New York"},
    {"customer_id": "C-104", "customer": "Windy City Wheels", "customer_group": "Consumer", "country": "US", "city": "Chicago"},
    {"customer_id": "C-105", "customer": "Rocky Mountain Cycles", "customer_group": "Commercial", "country": "US", "city": "Denver"},
    {"customer_id": "C-106", "customer": "SoCal Bicycles", "customer_group": "Educational", "country": "US", "city": "San Diego"},
    {"customer_id": "C-107", "customer": "Fahrrad Wurm", "customer_group": "Commercial", "country": "DE", "city": "Heidelberg"},
    {"customer_id": "C-108", "customer": "Radsport Paul", "customer_group": "Commercial", "country": "DE", "city": "Hamburg"},
    {"customer_id": "C-109", "customer": "Neckar Rad", "customer_group": "Consumer", "country": "DE", "city": "Stuttgart"},
    {"customer_id": "C-110", "customer": "Bavaria Velo", "customer_group": "Consumer", "country": "DE", "city": "Nürnberg"},
    {"customer_id": "C-111", "customer": "Hanseatische Räder", "customer_group": "Educational", "country": "DE", "city": "Bremen"},
    {"customer_id": "C-112", "customer": "Alpenbike München", "customer_group": "Commercial", "country": "DE", "city": "München"},
]

GBI_PRODUCTS = [
    # Bikes - Division BI
    # Notice: unit_price and unit_cogm are calibrated so some products are > 46% margin and some are < 46% margin!
    {"product_id": "PRD-B01", "product": "Air Hawk Black", "category": "Air Hawk", "division": "BI", "unit_price": 3200, "unit_cogm": 1600}, # 50.0% margin (>46%)
    {"product_id": "PRD-B02", "product": "Air Hawk Silver", "category": "Air Hawk", "division": "BI", "unit_price": 3100, "unit_cogm": 1750}, # 43.5% margin (<46%)
    {"product_id": "PRD-B03", "product": "Fly Deluxe Red", "category": "Fly Deluxe", "division": "BI", "unit_price": 2800, "unit_cogm": 1400}, # 50.0% margin (>46%)
    {"product_id": "PRD-B04", "product": "Fly Deluxe White", "category": "Fly Deluxe", "division": "BI", "unit_price": 2750, "unit_cogm": 1550}, # 43.6% margin (<46%)
    {"product_id": "PRD-B05", "product": "Offroad Pro 29", "category": "Offroad", "division": "BI", "unit_price": 2400, "unit_cogm": 1250}, # 47.9% margin (>46%)
    {"product_id": "PRD-B06", "product": "Offroad Comp 27.5", "category": "Offroad", "division": "BI", "unit_price": 2100, "unit_cogm": 1200}, # 42.9% margin (<46%)
    {"product_id": "PRD-B07", "product": "Touring Men Black", "category": "Touring", "division": "BI", "unit_price": 2600, "unit_cogm": 1350}, # 48.1% margin (>46%)
    {"product_id": "PRD-B08", "product": "Touring Women Silver", "category": "Touring", "division": "BI", "unit_price": 2550, "unit_cogm": 1480}, # 42.0% margin (<46%)
    # Accessories - Division AS
    {"product_id": "PRD-A01", "product": "Water Bottle Cage", "category": "Accessories", "division": "AS", "unit_price": 25, "unit_cogm": 10}, # 60.0% margin (>46%)
    {"product_id": "PRD-A02", "product": "Bike Helmet Pro", "category": "Accessories", "division": "AS", "unit_price": 95, "unit_cogm": 45}, # 52.6% margin (>46%)
    {"product_id": "PRD-A03", "product": "First Aid Kit", "category": "Accessories", "division": "AS", "unit_price": 40, "unit_cogm": 24}, # 40.0% margin (<46%)
    {"product_id": "PRD-A04", "product": "Repair Kit & Levers", "category": "Accessories", "division": "AS", "unit_price": 30, "unit_cogm": 17}, # 43.3% margin (<46%)
    {"product_id": "PRD-A05", "product": "Air Pump Mini", "category": "Accessories", "division": "AS", "unit_price": 35, "unit_cogm": 18}, # 48.6% margin (>46%)
]

SALES_ORGS = {
    "US": ["DN00", "DS00"],
    "DE": ["DB00", "DS01"],
}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def generate_gbi_dataset(target_rows=195):
    """Generates synthetic GBI sales transaction records."""
    orders = []
    
    # Seasonality weights for bicycle sales (Spring/Summer peak: Apr-Aug)
    seasonality = {
        1: 0.6, 2: 0.7, 3: 1.0, 4: 1.3, 5: 1.5, 6: 1.6,
        7: 1.5, 8: 1.4, 9: 1.1, 10: 0.9, 11: 0.7, 12: 0.8
    }

    # Ensure strong representation of 2019 for View 3 (Jan-Dec) and last 3 years (2017-2019)
    # Target breakdown: 2015: 20 rows, 2016: 25 rows, 2017: 35 rows, 2018: 45 rows, 2019: 70 rows (Total = 195)
    year_distribution = {
        2015: 20,
        2016: 25,
        2017: 35,
        2018: 45,
        2019: 70
    }

    order_counter = 10001

    for year, row_count in year_distribution.items():
        # For 2019, guarantee at least 4 records per month across categories for smooth seasonal curves
        months_pool = []
        if year == 2019:
            # 12 months * 4 categories = 48 baseline guaranteed rows
            for m in range(1, 13):
                for cat in ["Air Hawk", "Fly Deluxe", "Offroad", "Touring"]:
                    months_pool.append((m, cat))
            remaining = row_count - len(months_pool)
            for _ in range(max(0, remaining)):
                m_rand = random.choices(range(1, 13), weights=[seasonality[i] for i in range(1, 13)])[0]
                months_pool.append((m_rand, None))
        else:
            for _ in range(row_count):
                m_rand = random.choices(range(1, 13), weights=[seasonality[i] for i in range(1, 13)])[0]
                months_pool.append((m_rand, None))

        for month, forced_cat in months_pool:
            day = random.randint(1, 28)
            order_date = datetime.date(year, month, day)
            quarter = f"Q{(month - 1) // 3 + 1}"
            
            cust = random.choice(GBI_CUSTOMERS)
            sales_org = random.choice(SALES_ORGS[cust["country"]])
            
            if forced_cat:
                candidate_products = [p for p in GBI_PRODUCTS if p["category"] == forced_cat]
            else:
                candidate_products = GBI_PRODUCTS
            prod = random.choice(candidate_products)
            
            # Realistic quantities: bikes 1-15 units, accessories 5-60 units
            if prod["division"] == "BI":
                base_qty = random.randint(1, 12)
                # Boost during peak season
                if month in [4, 5, 6, 7, 8]:
                    base_qty = int(base_qty * 1.3) + 1
            else:
                base_qty = random.randint(5, 50)
                
            qty = max(1, base_qty)
            gross_revenue = round(qty * prod["unit_price"], 2)
            total_cogm = round(qty * prod["unit_cogm"], 2)
            
            # Discounts: 0% to 12%
            discount_pct = random.choices([0.0, 0.03, 0.05, 0.08, 0.10], weights=[0.4, 0.2, 0.2, 0.1, 0.1])[0]
            discount_usd = round(gross_revenue * discount_pct, 2)
            
            orders.append({
                "Sales_Order_ID": f"SO-{order_counter}",
                "Order_Date": order_date.strftime("%Y-%m-%d"),
                "Year": year,
                "Quarter": quarter,
                "Month": month,
                "Month_Name": MONTH_NAMES[month - 1],
                "Country": cust["country"],
                "Sales_Org": sales_org,
                "Division": prod["division"],
                "Customer_Group": cust["customer_group"],
                "Customer": cust["customer"],
                "Product_Category": prod["category"],
                "Product": prod["product"],
                "Sales_Quantity": qty,
                "Revenue_USD": gross_revenue,
                "COGM_USD": total_cogm,
                "Discount_USD": discount_usd,
            })
            order_counter += 1

    df_orders = pd.DataFrame(orders)
    df_customers = pd.DataFrame(GBI_CUSTOMERS)
    df_products = pd.DataFrame(GBI_PRODUCTS)

    return df_orders, df_customers, df_products

def export_data(base_dir=None):
    """Exports test dataset to Excel (.xlsx) and seeds local SQLite database."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    excel_path = os.path.join(base_dir, "gbi_test_data.xlsx")
    db_path = os.path.join(base_dir, "gbi_sales.db")

    print(f"Generating GBI test dataset...")
    df_orders, df_customers, df_products = generate_gbi_dataset()

    # 1. Export to Excel with multiple sheets
    print(f"Writing Excel file to {excel_path}...")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_orders.to_excel(writer, sheet_name="Sales_Orders", index=False)
        df_customers.to_excel(writer, sheet_name="Customers", index=False)
        df_products.to_excel(writer, sheet_name="Products", index=False)
    print(f"Excel export complete ({len(df_orders)} order rows).")

    # 2. Seed SQLite via SQLAlchemy
    print(f"Seeding SQLite database at {db_path}...")
    engine = create_engine(f"sqlite:///{db_path}")
    df_orders.to_sql("sales_orders", engine, if_exists="replace", index=False)
    df_customers.to_sql("customers", engine, if_exists="replace", index=False)
    df_products.to_sql("products", engine, if_exists="replace", index=False)
    print("SQLite database successfully populated.")

    return excel_path, db_path

if __name__ == "__main__":
    export_data()
