import sqlite3
from typing import Dict, List, Any


class SQLiteTool:
    """Tool for interacting with the Northwind SQLite database."""
    
    def __init__(self, db_path: str = "data/northwind.sqlite"):
        """
        Initialize the SQLite tool.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
    
    def get_schema(self) -> str:
        """
        Get the CREATE statements for the main tables.
        
        Returns:
            String containing CREATE TABLE/VIEW statements for Orders, Order Details, 
            Products, and Customers tables.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            tables = ['Orders', 'Order Details', 'Products', 'Customers']
            schema_statements = []
            
            for table in tables:
                # Query sqlite_master for the CREATE statement
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE name = ? AND type IN ('table', 'view')",
                    (table,)
                )
                result = cursor.fetchone()
                if result:
                    schema_statements.append(result[0])
            
            conn.close()
            return "\n\n".join(schema_statements)
        
        except Exception as e:
            return f"Error retrieving schema: {str(e)}"
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Dictionary with keys:
            - columns: List of column names
            - rows: List of rows (each row is a list of values)
            - error: Error message if any, empty string otherwise
        """
        result = {
            "columns": [],
            "rows": [],
            "error": ""
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(sql)
            
            # Get column names from cursor description
            if cursor.description:
                result["columns"] = [desc[0] for desc in cursor.description]
                result["rows"] = cursor.fetchall()
            
            conn.close()
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
