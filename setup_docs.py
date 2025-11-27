#!/usr/bin/env python3
"""
Setup script to create the required documentation files in the docs/ folder.
"""

import os


def create_docs():
    """Create the docs directory and write all required documentation files."""
    
    # Ensure docs directory exists
    os.makedirs("docs", exist_ok=True)
    print("✓ Created/verified docs/ directory")
    
    # File 1: marketing_calendar.md
    marketing_calendar = """# Northwind Marketing Calendar (1997)
## Summer Beverages 1997
- Dates: 1997-06-01 to 1997-06-30
- Notes: Focus on Beverages and Condiments.
## Winter Classics 1997
- Dates: 1997-12-01 to 1997-12-31
- Notes: Push Dairy Products and Confections for holiday gifting.
"""
    
    with open("docs/marketing_calendar.md", "w", encoding="utf-8") as f:
        f.write(marketing_calendar)
    print("✓ Created docs/marketing_calendar.md")
    
    # File 2: kpi_definitions.md
    kpi_definitions = """# KPI Definitions
## Average Order Value (AOV)
- AOV = SUM(UnitPrice * Quantity * (1 - Discount)) / COUNT(DISTINCT OrderID)
## Gross Margin
- GM = SUM((UnitPrice - CostOfGoods) * Quantity * (1 - Discount))
- If cost is missing, approximate with category-level average (document your approach).
"""
    
    with open("docs/kpi_definitions.md", "w", encoding="utf-8") as f:
        f.write(kpi_definitions)
    print("✓ Created docs/kpi_definitions.md")
    
    # File 3: catalog.md
    catalog = """# Catalog Snapshot
- Categories include Beverages, Condiments, Confections, Dairy Products, Grains/Cereals, Meat/Poultry, Produce, Seafood.
- Products map to categories as in the Northwind DB.
"""
    
    with open("docs/catalog.md", "w", encoding="utf-8") as f:
        f.write(catalog)
    print("✓ Created docs/catalog.md")
    
    # File 4: product_policy.md
    product_policy = """# Returns & Policy
- Perishables (Produce, Seafood, Dairy): 3–7 days.
- Beverages unopened: 14 days; opened: no returns.
- Non-perishables: 30 days.
"""
    
    with open("docs/product_policy.md", "w", encoding="utf-8") as f:
        f.write(product_policy)
    print("✓ Created docs/product_policy.md")
    
    print("\n" + "=" * 60)
    print("✓✓✓ All documentation files created successfully! ✓✓✓")
    print("=" * 60)
    print("\nCreated files:")
    print("  - docs/marketing_calendar.md")
    print("  - docs/kpi_definitions.md")
    print("  - docs/catalog.md")
    print("  - docs/product_policy.md")


if __name__ == "__main__":
    create_docs()
