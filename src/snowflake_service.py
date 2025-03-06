"""
Snowflake Service Module

This module provides a service for interacting with Snowflake databases.
It handles connections, query execution, and result formatting.
"""

import os
import logging
import pandas as pd
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Tuple, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import snowflake.connector
from snowflake.connector.errors import DatabaseError, ProgrammingError, OperationalError

# Load environment variables
load_dotenv()

# Configure logging - Fix LOG_LEVEL parsing issue
log_level_str = os.environ.get("LOG_LEVEL", "INFO")
# Extract just the level name if there are comments
if "#" in log_level_str:
    log_level_str = log_level_str.split("#")[0].strip()
    
logging.basicConfig(
    level=log_level_str,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("snowflake_service")  # Use a more specific logger name


class SnowflakeService:
    """Service for interacting with Snowflake databases."""

    def __init__(self):
        """Initialize the Snowflake service."""
        self.conn = None
        self.cursor = None
        self.connected = False
        
        # Use the full account string as provided (including region)
        self.connection_params = {
            "user": os.environ.get("SNOWFLAKE_USER"),
            "password": os.environ.get("SNOWFLAKE_PASSWORD"),
            "account": os.environ.get("SNOWFLAKE_ACCOUNT"),
            "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE"),
            "database": os.environ.get("SNOWFLAKE_DATABASE"),
            "schema": os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC"),
        }
        
        # Optional role parameter
        role = os.environ.get("SNOWFLAKE_ROLE")
        if role:
            self.connection_params["role"] = role

    def connect(self) -> bool:
        """
        Establish a connection to Snowflake.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            logger.info("Connecting to Snowflake...")
            self.conn = snowflake.connector.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            self.connected = True
            logger.info("Connected to Snowflake successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            self.connected = False
            return False

    def close(self) -> None:
        """Close the Snowflake connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("Snowflake connection closed")
        except Exception as e:
            logger.error(f"Error closing Snowflake connection: {str(e)}")
        finally:
            self.connected = False
            self.cursor = None
            self.conn = None

    @retry(
        retry=retry_if_exception_type(OperationalError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def execute_query(self, query: str) -> Tuple[bool, Union[pd.DataFrame, str]]:
        """
        Execute a query on Snowflake and return the results.
        
        Args:
            query (str): The SQL query to execute
            
        Returns:
            Tuple[bool, Union[pd.DataFrame, str]]: A tuple containing:
                - bool: True if query was successful, False otherwise
                - Union[pd.DataFrame, str]: DataFrame with results if successful, error message if not
        """
        if not self.connected:
            success = self.connect()
            if not success:
                return False, "Failed to connect to Snowflake"

        try:
            logger.info(f"Executing query: {query}")
            self.cursor.execute(query)
            
            # Get column names
            columns = [col[0] for col in self.cursor.description] if self.cursor.description else []
            
            # Fetch all results
            data = self.cursor.fetchall()
            
            # Convert to DataFrame
            if data and columns:
                df = pd.DataFrame(data, columns=columns)
                return True, df
            elif not data:
                return True, pd.DataFrame(columns=columns)
            else:
                return True, "Query executed successfully, but no results were returned"
                
        except (DatabaseError, ProgrammingError) as e:
            error_msg = f"Query execution error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except OperationalError as e:
            logger.warning(f"Operational error (will retry): {str(e)}")
            # This error will trigger a retry
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in the current database and schema.
        
        Args:
            schema (Optional[str]): The schema to list tables from. If None, uses the default schema.
            
        Returns:
            List[str]: A list of table names
        """
        schema_name = schema or self.connection_params["schema"]
        query = f"SHOW TABLES IN {self.connection_params['database']}.{schema_name}"
        success, result = self.execute_query(query)
        
        if success and isinstance(result, pd.DataFrame) and not result.empty:
            # The "name" column contains table names
            if "name" in result.columns:
                return result["name"].tolist()
        
        return []

    def get_table_schema(self, table_name: str, schema: Optional[str] = None) -> Dict[str, str]:
        """
        Get the schema of a table.
        
        Args:
            table_name (str): The name of the table
            schema (Optional[str]): The schema containing the table. If None, uses the default schema.
            
        Returns:
            Dict[str, str]: A dictionary mapping column names to their data types
        """
        schema_name = schema or self.connection_params["schema"]
        query = f"DESCRIBE TABLE {self.connection_params['database']}.{schema_name}.{table_name}"
        success, result = self.execute_query(query)
        
        if success and isinstance(result, pd.DataFrame) and not result.empty:
            # Extract column names and types
            if "name" in result.columns and "type" in result.columns:
                return dict(zip(result["name"], result["type"]))
        
        return {}

    def format_results(self, results: pd.DataFrame, max_rows: int = 20) -> str:
        """
        Format DataFrame results as a readable string.
        
        Args:
            results (pd.DataFrame): The DataFrame to format
            max_rows (int): Maximum number of rows to include
            
        Returns:
            str: Formatted results as a string
        """
        if results.empty:
            return "No results found."
        
        # Limit the number of rows
        if len(results) > max_rows:
            display_df = results.head(max_rows)
            footer = f"\n... and {len(results) - max_rows} more rows"
        else:
            display_df = results
            footer = ""
        
        # Use tabulate to format as a table
        from tabulate import tabulate
        table_str = tabulate(display_df, headers='keys', tablefmt='grid', showindex=False)
        
        # Add row count
        header = f"Results: {len(results)} rows total\n"
        
        return header + table_str + footer

    def natural_language_to_sql(self, question: str) -> str:
        """
        Convert a natural language question to SQL.
        In a production system, this would use an LLM or similar technology.
        
        Args:
            question (str): The natural language question
            
        Returns:
            str: The corresponding SQL query
        """
        # This is a simplified implementation
        # In a real implementation, you would call an LLM API here
        
        # Simple keyword mapping
        if "list" in question.lower() or "show" in question.lower() or "what are" in question.lower():
            if "table" in question.lower():
                return f"SHOW TABLES IN {self.connection_params['database']}.{self.connection_params['schema']}"
            
        # Default to a simple SELECT statement if table name can be detected
        tables = self.list_tables()
        for table in tables:
            if table.lower() in question.lower():
                return f"SELECT * FROM {table} LIMIT 10"
                
        return "SELECT 1"  # Fallback query


# Test functionality if the script is run directly
if __name__ == "__main__":
    print("=" * 80)
    print("Snowflake Service Test")
    print("=" * 80)
    
    # Initialize service
    snowflake = SnowflakeService()
    
    # Test 1: Connection
    print("\n1. Testing connection to Snowflake...")
    connected = snowflake.connect()
    print(f"Connection successful: {connected}")
    if not connected:
        print("Cannot proceed with tests without a connection.")
        exit(1)
        
    # Test 2: List tables
    print("\n2. Testing list_tables()...")
    schema = os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC")
    tables = snowflake.list_tables(schema)
    if tables:
        print(f"Found {len(tables)} tables in schema {schema}:")
        for table in tables:
            print(f"  - {table}")
    else:
        print(f"No tables found in schema {schema}")
    
    # Test 3: Table schema (if tables exist)
    if tables:
        print("\n3. Testing get_table_schema()...")
        table_name = tables[0]
        print(f"Getting schema for table: {table_name}")
        schema_info = snowflake.get_table_schema(table_name)
        if schema_info:
            print(f"Schema for {table_name}:")
            for column, data_type in schema_info.items():
                print(f"  - {column}: {data_type}")
        else:
            print(f"Failed to get schema for table {table_name}")
    
    # Test 4: Execute a simple query
    print("\n4. Testing execute_query()...")
    query = "SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
    print(f"Executing query: {query}")
    success, result = snowflake.execute_query(query)
    if success:
        if isinstance(result, pd.DataFrame):
            print("Query results:")
            print(snowflake.format_results(result))
        else:
            print(f"Query executed successfully: {result}")
    else:
        print(f"Query execution failed: {result}")
    
    # Test 5: Natural language to SQL (simple implementation)
    print("\n5. Testing natural_language_to_sql()...")
    nl_query = "Show me the tables in the database"
    sql = snowflake.natural_language_to_sql(nl_query)
    print(f"Natural language query: {nl_query}")
    print(f"Generated SQL: {sql}")
    
    # Test 6: Execute the generated SQL
    print("\n6. Testing execution of generated SQL...")
    success, result = snowflake.execute_query(sql)
    if success:
        if isinstance(result, pd.DataFrame):
            print("Query results:")
            print(snowflake.format_results(result))
        else:
            print(f"Query executed successfully: {result}")
    else:
        print(f"Query execution failed: {result}")
    
    # Close connection
    print("\nCleaning up...")
    snowflake.close()
    print("Tests completed.")
