#!/usr/bin/env python3
"""
Optimize the SQLGenerator component using DSPy's BootstrapFewShot.
This fulfills the assignment requirement to optimize at least one component.

IMPORTANT: You MUST have Ollama running before executing this script!
Run: ollama serve (in a separate terminal)
"""

import dspy
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.rag.tools.sqlite_tool import SQLiteTool
from agent.dspy_signatures import SQLGeneratorSignature


# Initialize database tool
db_tool = SQLiteTool(db_path="data/northwind.sqlite")

# Get schema for training examples
SCHEMA = db_tool.get_schema()


# Training Data: 5 handcrafted examples
trainset = [
    dspy.Example(
        question="How many products are in the Beverages category?",
        schema=SCHEMA,
        constraints="Use standard SQL syntax. Join tables appropriately.",
        sql_query="""SELECT COUNT(*) as product_count
FROM Products p
JOIN Categories c ON p.CategoryID = c.CategoryID
WHERE c.CategoryName = 'Beverages'"""
    ).with_inputs("question", "schema", "constraints"),
    
    dspy.Example(
        question="What is the total revenue from all orders?",
        schema=SCHEMA,
        constraints="Use standard SQL syntax. If CostOfGoods is missing, assume it is 0.7 * UnitPrice.",
        sql_query="""SELECT SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) as total_revenue
FROM [Order Details] od"""
    ).with_inputs("question", "schema", "constraints"),
    
    dspy.Example(
        question="List the top 5 customers by number of orders",
        schema=SCHEMA,
        constraints="Use standard SQL syntax. Join tables appropriately.",
        sql_query="""SELECT c.CustomerID, c.CompanyName, COUNT(o.OrderID) as order_count
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.CompanyName
ORDER BY order_count DESC
LIMIT 5"""
    ).with_inputs("question", "schema", "constraints"),
    
    dspy.Example(
        question="What is the average unit price of products supplied by each supplier?",
        schema=SCHEMA,
        constraints="Use standard SQL syntax. Join tables appropriately.",
        sql_query="""SELECT s.CompanyName, AVG(p.UnitPrice) as avg_price
FROM Products p
JOIN Suppliers s ON p.SupplierID = s.SupplierID
GROUP BY s.SupplierID, s.CompanyName
ORDER BY avg_price DESC"""
    ).with_inputs("question", "schema", "constraints"),
    
    dspy.Example(
        question="How many orders were shipped to France in 1997?",
        schema=SCHEMA,
        constraints="Use standard SQL syntax. Join tables appropriately.",
        sql_query="""SELECT COUNT(*) as order_count
FROM Orders
WHERE ShipCountry = 'France'
AND strftime('%Y', OrderDate) = '1997'"""
    ).with_inputs("question", "schema", "constraints")
]


def validate_sql(example, prediction, trace=None):
    """
    Metric function to validate SQL query execution.
    
    Args:
        example: The training example with expected output
        prediction: The model's prediction with sql_query field
        trace: Optional trace information (unused)
        
    Returns:
        True if SQL executes without error, False otherwise
    """
    # Get the predicted SQL query
    predicted_sql = prediction.sql_query if hasattr(prediction, 'sql_query') else str(prediction)
    
    # Try to execute the SQL
    result = db_tool.execute_query(predicted_sql)
    
    # Check if execution was successful (no error)
    if result.get("error"):
        print(f"  ✗ SQL Error: {result['error'][:100]}")
        return False
    else:
        print(f"  ✓ SQL executed successfully, returned {len(result.get('rows', []))} rows")
        return True


def main():
    """Main optimization function."""
    print("=" * 70)
    print("DSPy SQL Generator Optimization")
    print("=" * 70)
    
    # Check if database exists
    if not os.path.exists("data/northwind.sqlite"):
        print("\n✗ Error: Database file 'data/northwind.sqlite' not found!")
        print("  Please ensure the Northwind database is in the data/ folder.")
        sys.exit(1)
    
    print(f"\n✓ Loaded {len(trainset)} training examples")
    print("✓ Database connection verified")
    
    # Create the SQL Generator module to optimize
    print("\nInitializing SQL Generator module...")
    sql_generator = dspy.ChainOfThought(SQLGeneratorSignature)
    
    # Configure the optimizer
    print("\nConfiguring BootstrapFewShot optimizer...")
    print("  - Max bootstrapped demos: 3")
    print("  - Max labeled demos: 3")
    print("  - Metric: validate_sql (checks SQL execution)")
    
    optimizer = dspy.BootstrapFewShot(
        metric=validate_sql,
        max_bootstrapped_demos=3,
        max_labeled_demos=3
    )
    
    # Run optimization
    print("\n" + "=" * 70)
    print("Starting Optimization Process...")
    print("=" * 70)
    print("\nThis may take a few minutes as DSPy evaluates different prompts...")
    print("Ollama must be running for this to work!\n")
    
    try:
        optimized_generator = optimizer.compile(
            sql_generator,
            trainset=trainset
        )
        
        print("\n" + "=" * 70)
        print("✓ Optimization Complete!")
        print("=" * 70)
        
        # Save the optimized program
        output_path = "agent/sql_gen_optimized.json"
        optimized_generator.save(output_path)
        
        print(f"\n✓ Optimized SQL Generator saved to: {output_path}")
        
        # Test the optimized generator
        print("\n" + "=" * 70)
        print("Testing Optimized Generator")
        print("=" * 70)
        
        test_question = "How many orders were placed in 1996?"
        print(f"\nTest Question: {test_question}")
        
        result = optimized_generator(
            question=test_question,
            schema=SCHEMA,
            constraints="Use standard SQL syntax."
        )
        
        print(f"\nGenerated SQL:\n{result.sql_query}")
        
        # Validate the test query
        validation_result = db_tool.execute_query(result.sql_query)
        if validation_result.get("error"):
            print(f"\n✗ Validation Error: {validation_result['error']}")
        else:
            print(f"\n✓ Query executed successfully!")
            print(f"  Returned {len(validation_result.get('rows', []))} rows")
        
        print("\n" + "=" * 70)
        print("Optimization process completed successfully!")
        print("=" * 70)
        print("\nNext Steps:")
        print("1. The optimized model is saved in agent/sql_gen_optimized.json")
        print("2. Update agent/dspy_signatures.py to load this file")
        print("3. See instructions below for integration")
        
    except Exception as e:
        print(f"\n✗ Error during optimization: {e}")
        print("\nMake sure:")
        print("  1. Ollama is running (ollama serve)")
        print("  2. The phi3.5 model is downloaded (ollama pull phi3.5)")
        print("  3. The database exists at data/northwind.sqlite")
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "!" * 70)
    print("! REMINDER: Ollama MUST be running before executing this script!")
    print("! Run 'ollama serve' in a separate terminal first")
    print("!" * 70 + "\n")
    
    # Give user a chance to cancel
    import time
    time.sleep(2)
    
    main()
