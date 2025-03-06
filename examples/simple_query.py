#!/usr/bin/env python
"""
Simple Example: Connecting to Snowflake MCP

This script demonstrates how to connect to the Snowflake MCP server
and execute a simple query using the Python MCP client library.

Make sure the MCP server is running before executing this script.
"""

import os
import sys
import asyncio
import subprocess
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from mcp.client.client import Client
except ImportError:
    print("Error: MCP Python SDK not found.")
    print("Please install it using: pip install mcp")
    sys.exit(1)

# Load environment variables
load_dotenv()


async def main():
    """Main function demonstrating MCP client usage."""
    print("Connecting to Snowflake MCP...")
    
    # Start the MCP server in a separate process
    server_process = subprocess.Popen(
        [sys.executable, "../src/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Create client and connect
    client = Client(stdio_process=server_process)
    await client.connect()
    
    try:
        # List available tables
        print("\n--- Listing Tables ---")
        tables_result = await client.tools.list_tables()
        
        if tables_result["success"]:
            print(f"Found tables: {tables_result['tables']}")
        else:
            print(f"Error: {tables_result['message']}")
        
        # Example: Get schema of a table
        if tables_result["success"] and tables_result["tables"]:
            example_table = tables_result["tables"][0]
            print(f"\n--- Getting Schema for {example_table} ---")
            
            schema_result = await client.tools.get_table_schema(
                table_name=example_table
            )
            
            if schema_result["success"]:
                print("Table Schema:")
                for column, data_type in schema_result["columns"].items():
                    print(f"  {column}: {data_type}")
            else:
                print(f"Error: {schema_result['message']}")
        
        # Example: Execute a natural language query
        print("\n--- Executing Natural Language Query ---")
        query_result = await client.tools.query_database(
            query="Show me the first 5 rows from one of the tables",
            is_natural_language=True,
            max_rows=5
        )
        
        if query_result["success"]:
            print(f"SQL Query: {query_result['sql']}")
            print("Results:")
            print(query_result["results"])
        else:
            print(f"Error: {query_result['message']}")
        
        # Example: Execute a direct SQL query
        print("\n--- Executing SQL Query ---")
        sql_query = "SELECT 1 as test_column"  # Simple test query
        
        query_result = await client.tools.query_database(
            query=sql_query,
            is_natural_language=False
        )
        
        if query_result["success"]:
            print("Results:")
            print(query_result["results"])
        else:
            print(f"Error: {query_result['message']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Close the client connection
        await client.close()
        
        # Terminate the server process
        server_process.terminate()
        server_process.wait()
        print("\nConnection closed.")


if __name__ == "__main__":
    asyncio.run(main()) 