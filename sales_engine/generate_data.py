"""
Synthetic sales data generator.
Produces realistic multi-year transactional sales data with
seasonality, so the KPI queries have real trends to discover.
"""
import random
import csv
from datetime import date, timedelta

random.seed(42)

CATEGORIES = {
    "Technology": ["Laptops", "Monitors", "Accessories", "Networking"],
    "Furniture": ["Chairs", "Desks", "Storage", "Lighting"],
    "Office Supplies": ["Paper", "Binders", "Pens", "Labels"],
    "Electronics": ["Audio", "Cameras", "Wearables", "Smart Home"],
}

PRODUCT_NAMES = {
    "Laptops": ["UltraBook Pro 14", "SlimTop 13", "PowerNote X"],
    "Monitors": ["UltraHD Monitor 27", "ClearView 24", "CurveMax 32"],
    "Accessories": ["Wireless Mouse", "Mechanical Keyboard", "USB-C Hub"],
    "Networking": ["Mesh Router AC", "Gigabit Switch 8", "WiFi Extender"],
    "Chairs": ["ErgoChair Pro", "MeshBack Task Chair", "Executive Recliner"],
    "Desks": ["StandDesk Adjustable", "Corner Workstation", "Compact Desk"],
    "Storage": ["Filing Cabinet 3-Drawer", "Bookshelf Oak", "Storage Bin Set"],
    "Lighting": ["LED Desk Lamp", "Floor Lamp Modern", "Task Light Clip"],
    "Paper": ["Copy Paper Ream", "Sticky Notes Pack", "Notebook Set"],
    "Binders": ["3-Ring Binder", "Report Cover", "Expanding File"],
    "Pens": ["Gel Pen Pack", "Fine Liner Set", "Highlighter Pack"],
    "Labels": ["Shipping Labels", "Address Labels", "Color Dot Labels"],
    "Audio": ["Bluetooth Speaker Mini", "Noise Cancel Headphones", "Soundbar Compact"],
    "Cameras": ["Webcam 4K HD", "Action Cam Mini", "Security Cam Indoor"],
    "Wearables": ["Fitness Tracker", "Smartwatch Series X", "Sleep Tracker Band"],
    "Smart Home": ["Smart Plug 2-Pack", "Video Doorbell", "Smart Bulb Kit"],
}

REGIONS = {
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": ["Germany", "France", "United Kingdom"],
    "Asia Pacific": ["India", "Australia", "Japan"],
}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]

FIRST_NAMES = ["James","Priya","Wei","Maria","Ahmed","Olivia","Noah","Emma","Liam","Sophia",
               "Raj","Anna","Carlos","Yuki","Fatima","Lucas","Mia","Ethan","Ivy","Omar"]
LAST_NAMES = ["Smith","Sharma","Chen","Garcia","Khan","Brown","Wilson","Martinez","Lee","Davis",
              "Patel","Rossi","Kim","Müller","Ali","Nguyen","Johnson","Clark","Singh","Ito"]


def build_dim_product(path):
    rows, pid = [], 1
    for cat, subs in CATEGORIES.items():
        for sub in subs:
            for name in PRODUCT_NAMES[sub]:
                unit_cost = round(random.uniform(8, 400), 2)
                rows.append([pid, name, cat, sub, unit_cost])
                pid += 1
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_id","product_name","category","sub_category","unit_cost"])
        w.writerows(rows)
    return rows


def build_dim_customer(path, n=60):
    rows = []
    for cid in range(1, n + 1):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        region = random.choice(list(REGIONS.keys()))
        country = random.choice(REGIONS[region])
        segment = random.choice(SEGMENTS)
        rows.append([cid, name, segment, country, region])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["customer_id","customer_name","segment","country","region"])
        w.writerows(rows)
    return rows


def build_dim_date(path, start_year=2022, years=3):
    rows = []
    start = date(start_year, 1, 1)
    end = date(start_year + years, 1, 1)
    d = start
    while d < end:
        rows.append([
            d.isoformat(), d.day, d.month, d.strftime("%B"),
            (d.month - 1)//3 + 1, d.year, 1 if d.weekday() >= 5 else 0
        ])
        d += timedelta(days=1)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date_id","day","month","month_name","quarter","year","is_weekend"])
        w.writerows(rows)
    return rows


def build_fact_sales(path, products, customers, dates, n_rows=50000):
    rows = []
    dates_list = [r[0] for r in dates]
    # weight recent + Nov/Dec (seasonality) more heavily
    date_weights = []
    for r in dates:
        month = r[2]
        w = 1.0
        if month in (11, 12):
            w = 2.2          # holiday season bump
        elif month in (6, 7):
            w = 1.4
        date_weights.append(w)

    line_id = 1
    order_counter = 1
    for _ in range(n_rows):
        d = random.choices(dates_list, weights=date_weights, k=1)[0]
        cust = random.choice(customers)
        prod = random.choice(products)
        qty = random.randint(1, 8)
        unit_cost = prod[4]
        unit_price = round(unit_cost * random.uniform(1.3, 2.4), 2)
        discount = round(random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2]), 2)
        sales_amount = round(qty * unit_price * (1 - discount), 2)
        profit = round(sales_amount - qty * unit_cost, 2)

        if random.random() < 0.35:
            order_counter += 1
        order_id = f"ORD-{order_counter:06d}"

        ship_offset = random.randint(1, 7)
        try:
            y, m, dd = map(int, d.split("-"))
            ship_date = (date(y, m, dd) + timedelta(days=ship_offset)).isoformat()
        except Exception:
            ship_date = d

        rows.append([
            line_id, order_id, d, ship_date, cust[0], prod[0],
            qty, unit_price, discount, sales_amount, profit
        ])
        line_id += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["line_id","order_id","order_date","ship_date","customer_id",
                     "product_id","quantity","unit_price","discount","sales_amount","profit"])
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out, exist_ok=True)

    products = build_dim_product(os.path.join(out, "dim_product.csv"))
    customers = build_dim_customer(os.path.join(out, "dim_customer.csv"), n=60)
    dates = build_dim_date(os.path.join(out, "dim_date.csv"), start_year=2022, years=3)
    sales = build_fact_sales(os.path.join(out, "fact_sales.csv"), products, customers, dates, n_rows=500000)

    print(f"Generated: {len(products)} products, {len(customers)} customers, "
          f"{len(dates)} dates, {len(sales)} sales rows")
