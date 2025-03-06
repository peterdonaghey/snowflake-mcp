# Snowflake MCP Examples

This directory contains examples and instructions for interacting with the Snowflake MCP server.

## Using the MCP CLI

The easiest way to interact with the Snowflake MCP server is using the MCP Inspector tool that comes with the MCP CLI.

### Running the Server with Inspector

```bash
# Start the server with the development UI
mcp dev src/server.py
```

This command starts the server and opens the MCP Inspector in your web browser, allowing you to:

1. View server information
2. Try out the available tools
3. See logs and debug information

### Installing in Claude Desktop

To use the server with Claude Desktop:

```bash
# Install the server in Claude Desktop
mcp install src/server.py
```

After installation, you can select the Snowflake MCP server in Claude Desktop's settings.

### Running in Standard Mode

For production use:

```bash
# Run the server in standard mode
mcp run src/server.py
```

## Available Tools

The Snowflake MCP server provides the following tools:

1. **query_database** - Execute SQL or natural language queries on the Snowflake database

   - Parameters:
     - `query`: The SQL query or natural language question
     - `is_natural_language`: Boolean flag (default: false)
     - `max_rows`: Maximum number of rows to return (default: 20)

2. **list_tables** - List all tables in the database

   - Parameters:
     - `schema`: Optional schema name

3. **get_table_schema** - Get the schema of a specific table
   - Parameters:
     - `table_name`: The name of the table
     - `schema`: Optional schema name

## Example Queries

Here are some examples you can try in the MCP Inspector:

### SQL Query

```
SELECT * FROM your_table LIMIT 10
```

### Natural Language Query

```
Show me the first 5 rows from the customer table
```

### List Tables

```
List all tables in the reports schema
```

### Get Table Schema

```
Show me the columns in the orders table
```
