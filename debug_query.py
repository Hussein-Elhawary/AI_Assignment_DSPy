import sqlite3

conn = sqlite3.connect('agent/rag/northwind.db')
c = conn.cursor()

# Test the exact query
query = "SELECT COUNT(DISTINCT OrderID) AS NumberOfOrders FROM Orders WHERE strftime('%Y', OrderDate) = '1997';"
c.execute(query)
result = c.fetchall()
print(f"Query result: {result}")

# Check what strftime returns
c.execute("SELECT OrderDate, strftime('%Y', OrderDate) as year FROM Orders LIMIT 10")
dates = c.fetchall()
print("\nDate conversions:")
for date in dates:
    print(f"  {date}")

# Count orders with simple LIKE
c.execute("SELECT COUNT(*) FROM Orders WHERE OrderDate LIKE '1997%'")
like_result = c.fetchone()
print(f"\nUsing LIKE '1997%': {like_result[0]}")

conn.close()
