import sqlite3

conn = sqlite3.connect('agent/rag/northwind.db')
c = conn.cursor()

# First, let's see what tables exist
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", tables)

# Check the Orders table structure
c.execute("PRAGMA table_info(Orders)")
columns = c.fetchall()
print("\nOrders columns:", columns)

# Get some sample data
c.execute("SELECT * FROM Orders LIMIT 5")
rows = c.fetchall()
print("\nSample data:")
for row in rows:
    print(row)

conn.close()
