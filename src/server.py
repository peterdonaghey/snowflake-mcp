#!/usr/bin/env python
"""
Snowflake MCP Server

This server implements the Model Context Protocol (MCP) to allow Claude and other
LLM assistants to interact with Snowflake databases through natural language.

Usage:
    mcp dev server.py    # Run with MCP Inspector interface
    mcp run server.py    # Run in standard mode
    mcp install server.py # Install in Claude Desktop
    python server.py     # Run directly

Environment Variables:
    See .env.sample for required environment variables
"""

import os
import sys
import json
import logging
import atexit
from typing import Dict, Any, List, Optional
import pandas as pd
from dotenv import load_dotenv

try:
    # Import the official MCP Python SDK
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: MCP Python SDK not found.")
    print("Please install it using: pip install mcp")
    sys.exit(1)

from snowflake_service import SnowflakeService

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("snowflake_mcp.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Snowflake service
snowflake = SnowflakeService()

# Initialize the FastMCP server - this is the main exported object
mcp = FastMCP(
    name=os.environ.get("MCP_SERVER_NAME", "snowflake-mcp"), 
    version=os.environ.get("MCP_SERVER_VERSION", "1.0.0")
)

# Helper function to ensure we have a Snowflake connection
def ensure_connection() -> bool:
    """Ensure we have an active Snowflake connection."""
    # Always check if lazy initialization is enabled
    lazy_init = os.environ.get("SNOWFLAKE_LAZY_INIT", "false").lower() == "true"
    
    # For deployment environments, log but don't fail if we can't connect initially
    if lazy_init and not snowflake.connected:
        try:
            logger.info("Lazily establishing Snowflake connection...")
            return snowflake.connect()
        except Exception as e:
            logger.warning(f"Lazy connection initialization failed, will retry on first request: {str(e)}")
            return False
            
    # Standard connection check for non-lazy mode
    if not snowflake.connected:
        logger.info("Establishing Snowflake connection...")
        return snowflake.connect()
    return True

# Query Database Tool
@mcp.tool(description="Execute an SQL query or natural language query on the Snowflake database")
def query_database(
    query: str, 
    is_natural_language: bool = False, 
    max_rows: int = 20
) -> Dict[str, Any]:
    """
    Execute a query on the Snowflake database.
    
    Args:
        query: The SQL query or natural language question to execute
        is_natural_language: Whether the query is in natural language (true) or SQL (false)
        max_rows: Maximum number of rows to return
        
    Returns:
        Dictionary with query results and status
    """
    logger.info(f"Handling query_database request: {query}")
    
    if not query:
        return {
            "success": False,
            "message": "Query cannot be empty",
            "results": "",
            "sql": ""
        }
    
    # Ensure Snowflake connection
    if not ensure_connection():
        return {
            "success": False,
            "message": "Failed to connect to Snowflake",
            "results": "",
            "sql": query
        }
    
    # If it's a natural language query, convert it to SQL
    sql_query = snowflake.natural_language_to_sql(query) if is_natural_language else query
    
    # Execute the query
    success, result = snowflake.execute_query(sql_query)
    
    if success:
        if isinstance(result, pd.DataFrame):
            formatted_results = snowflake.format_results(result, max_rows)
            return {
                "success": True,
                "message": "Query executed successfully",
                "results": formatted_results,
                "sql": sql_query
            }
        else:
            return {
                "success": True,
                "message": str(result),
                "results": str(result),
                "sql": sql_query
            }
    else:
        return {
            "success": False,
            "message": str(result),
            "results": "",
            "sql": sql_query
        }
        
# List Tables Tool
@mcp.tool(description="List all tables in the database")
def list_tables(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """
    List all tables in the database.
    
    Args:
        schema_name: The schema to list tables from (optional)
        
    Returns:
        Dictionary with list of tables and status
    """
    logger.info(f"Handling list_tables request for schema: {schema_name}")
    
    # Ensure Snowflake connection
    if not ensure_connection():
        return {
            "success": False,
            "message": "Failed to connect to Snowflake",
            "tables": []
        }
    
    try:
        tables = snowflake.list_tables(schema_name)
        return {
            "success": True,
            "message": f"Found {len(tables)} tables",
            "tables": tables
        }
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return {
            "success": False,
            "message": f"Error listing tables: {str(e)}",
            "tables": []
        }
        
# Get Table Schema Tool
@mcp.tool(description="Get the schema of a specific table")
def get_table_schema(table_name: str, schema_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the schema of a table.
    
    Args:
        table_name: The name of the table
        schema_name: The schema containing the table (optional)
        
    Returns:
        Dictionary with table schema and status
    """
    logger.info(f"Handling get_table_schema request for table: {table_name} in schema: {schema_name}")
    
    # Ensure Snowflake connection
    if not ensure_connection():
        return {
            "success": False,
            "message": "Failed to connect to Snowflake",
            "schema": {}
        }
    
    try:
        schema = snowflake.get_table_schema(table_name, schema_name)
        return {
            "success": True,
            "message": f"Retrieved schema for table {table_name}",
            "schema": schema
        }
    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting table schema: {str(e)}",
            "schema": {}
        }

# Handle graceful shutdown
def cleanup():
    """Cleanup resources when the script exits."""
    logger.info("Cleaning up resources...")
    if snowflake.connected:
        snowflake.close()
        logger.info("Snowflake connection closed")

# Register the cleanup function to run at exit
atexit.register(cleanup)

# Standalone execution
if __name__ == "__main__":
    # Check for lazy initialization flag
    lazy_init = os.environ.get("SNOWFLAKE_LAZY_INIT", "false").lower() == "true"
    
    # Only try to establish initial connection if not in lazy mode
    if not lazy_init:
        logger.info("Starting Snowflake MCP server with eager connection...")
        if not ensure_connection():
            logger.warning("Failed to establish initial Snowflake connection. Will retry on first request.")
    else:
        logger.info("Starting Snowflake MCP server with lazy connection initialization...")
        logger.info("Snowflake connection will be established on first request.")

    # Run the MCP server directly (SDK will handle transport)
    logger.info("Starting MCP server...")
    mcp.run()
