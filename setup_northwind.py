"""
Setup script to create and populate Northwind database with sample data.
"""
import sqlite3
import os

db_path = "agent/rag/northwind.db"

# Remove existing database if it exists
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create Orders table
cursor.execute("""
CREATE TABLE Orders (
    OrderID INTEGER PRIMARY KEY,
    CustomerID TEXT,
    OrderDate TEXT,
    ShipperID INTEGER
)
""")

# Create [Order Details] table
cursor.execute("""
CREATE TABLE [Order Details] (
    OrderDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
    OrderID INTEGER,
    ProductID INTEGER,
    Quantity INTEGER,
    UnitPrice REAL,
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
)
""")

# Create Products table
cursor.execute("""
CREATE TABLE Products (
    ProductID INTEGER PRIMARY KEY,
    ProductName TEXT,
    CategoryID INTEGER,
    Unit TEXT,
    Price REAL
)
""")

# Create Customers table
cursor.execute("""
CREATE TABLE Customers (
    CustomerID TEXT PRIMARY KEY,
    CustomerName TEXT,
    ContactName TEXT,
    Country TEXT
)
""")

# Insert sample customers
customers_data = [
    ('ALFKI', 'Alfreds Futterkiste', 'Maria Anders', 'Germany'),
    ('ANATR', 'Ana Trujillo Emparedados', 'Ana Trujillo', 'Mexico'),
    ('ANTON', 'Antonio Moreno Taquería', 'Antonio Moreno', 'Mexico'),
    ('BERGS', 'Berglunds snabbköp', 'Christina Berglund', 'Sweden'),
    ('BLAUS', 'Blauer See Delikatessen', 'Hanna Moos', 'Germany'),
]
cursor.executemany("INSERT INTO Customers VALUES (?, ?, ?, ?)", customers_data)

# Insert sample products
products_data = [
    (1, 'Chai', 1, '10 boxes x 20 bags', 18.00),
    (2, 'Chang', 1, '24 - 12 oz bottles', 19.00),
    (3, 'Aniseed Syrup', 2, '12 - 550 ml bottles', 10.00),
    (4, 'Chef Anton\'s Cajun Seasoning', 2, '48 - 6 oz jars', 22.00),
    (5, 'Grandma\'s Boysenberry Spread', 2, '12 - 8 oz jars', 25.00),
]
cursor.executemany("INSERT INTO Products VALUES (?, ?, ?, ?, ?)", products_data)

# Insert sample orders from 1996-1998
orders_data = [
    # 1996 orders
    (10248, 'ALFKI', '1996-07-04', 3),
    (10249, 'ANATR', '1996-07-05', 1),
    (10250, 'BERGS', '1996-07-08', 2),
    # 1997 orders
    (10251, 'ALFKI', '1997-01-15', 1),
    (10252, 'ANTON', '1997-02-20', 2),
    (10253, 'BERGS', '1997-03-12', 3),
    (10254, 'BLAUS', '1997-04-18', 1),
    (10255, 'ALFKI', '1997-05-22', 2),
    (10256, 'ANATR', '1997-06-30', 3),
    (10257, 'ANTON', '1997-07-14', 1),
    (10258, 'BERGS', '1997-08-25', 2),
    (10259, 'BLAUS', '1997-09-10', 3),
    (10260, 'ALFKI', '1997-10-05', 1),
    (10261, 'ANATR', '1997-11-18', 2),
    (10262, 'ANTON', '1997-12-22', 3),
    # 1998 orders
    (10263, 'BERGS', '1998-01-10', 1),
    (10264, 'BLAUS', '1998-02-14', 2),
    (10265, 'ALFKI', '1998-03-20', 3),
]
cursor.executemany("INSERT INTO Orders VALUES (?, ?, ?, ?)", orders_data)

# Insert sample order details
order_details_data = [
    (10248, 1, 12, 14.00),
    (10248, 2, 10, 9.80),
    (10249, 3, 5, 10.00),
    (10250, 4, 15, 22.00),
    (10251, 1, 20, 18.00),
    (10252, 2, 8, 19.00),
    (10253, 3, 10, 10.00),
    (10254, 4, 12, 22.00),
    (10255, 5, 6, 25.00),
    (10256, 1, 15, 18.00),
    (10257, 2, 18, 19.00),
    (10258, 3, 7, 10.00),
    (10259, 4, 9, 22.00),
    (10260, 5, 11, 25.00),
    (10261, 1, 14, 18.00),
    (10262, 2, 16, 19.00),
    (10263, 3, 8, 10.00),
    (10264, 4, 13, 22.00),
    (10265, 5, 10, 25.00),
]
for detail in order_details_data:
    cursor.execute("INSERT INTO [Order Details] (OrderID, ProductID, Quantity, UnitPrice) VALUES (?, ?, ?, ?)", detail)

conn.commit()

# Verify data
cursor.execute("SELECT COUNT(*) FROM Orders WHERE strftime('%Y', OrderDate) = '1997'")
count_1997 = cursor.fetchone()[0]
print(f"✓ Created Northwind database at {db_path}")
print(f"✓ Inserted {len(customers_data)} customers")
print(f"✓ Inserted {len(products_data)} products")
print(f"✓ Inserted {len(orders_data)} orders")
print(f"✓ Orders in 1997: {count_1997}")

conn.close()
