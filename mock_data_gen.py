import csv
import random
import datetime
import os
from dateutil.relativedelta import relativedelta

OUTPUT_DIR = os.path.join("data", "input")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration
NUM_ROWS = 500
DIRTY_PERCENTAGE = 0.10  # 10% of data will be dirty
ENCODINGS = ["utf-8", "latin-1", "iso-8859-1"]

# Mock Data Source
PRODUCTS = [
    ("Laptop", 1200.00),
    ("Mouse", 25.50),
    ("Keyboard", 45.00),
    ("Monitor", 300.00),
    ("HDMI Cable", 15.00),
    ("Headphones", 80.00),
]
STORES = [101, 102, 103, 104, 105]

def random_date(start_year=2025):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date.today()
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def dirty_price(price):
    case = random.randint(1, 4)
    if case == 1: return f"${price:,.2f}"
    if case == 2: return f"USD {price}"
    if case == 3: return f"{price} dollars"
    return f"{price}"  # Clean

def dirty_date(date_obj):
    case = random.randint(1, 4)
    if case == 1: return date_obj.strftime("%Y/%m/%d")
    if case == 2: return date_obj.strftime("%d-%m-%Y")
    if case == 3: return date_obj.strftime("%b %d, %Y")
    return date_obj.strftime("%Y-%m-%d") # Clean

def generate_row(row_id):
    product, base_price = random.choice(PRODUCTS)
    qty = random.randint(1, 5)
    
    # Base clean data
    date_val = random_date()
    price_val = base_price
    store_val = random.choice(STORES)
    
    # Introduce complications
    if random.random() < DIRTY_PERCENTAGE:
        error_type = random.choice(["price", "date", "id", "qty", "encoding_char"])
        
        if error_type == "price":
            price_val = dirty_price(base_price)
        elif error_type == "date":
            # Either format weirdly or make it invalid
            if random.random() < 0.3:
                date_val = "2025/13/45" # Invalid
            else:
                date_val = dirty_date(date_val)
        elif error_type == "id":
            row_id = "" # Empty ID
        elif error_type == "qty":
            qty = random.choice([-1, 0, "two"])
        elif error_type == "encoding_char":
            product = "Café " + product # Special char
            
    return [row_id, date_val, product, qty, price_val, store_val]

def main():
    today = datetime.date.today().strftime("%Y%m%d")
    filename = f"sales_{today}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    encoding = random.choice(ENCODINGS)
    print(f"Generating {filepath} with encoding: {encoding}")
    
    headers = ["ID", "Date", "Product", "Qty", "Price", "Store_ID"]
    
    rows = []
    for i in range(1, NUM_ROWS + 1):
        rows.append(generate_row(i))
        
    try:
        with open(filepath, "w", newline="", encoding=encoding) as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
