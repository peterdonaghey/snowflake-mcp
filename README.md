# Snowflake MCP (Model Context Protocol) Server

A Model Context Protocol (MCP) server implementation that allows AI assistants like Claude to interact with Snowflake databases through natural language queries.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Features

- Execute SQL queries on Snowflake databases via natural language
- Automatic database connection lifecycle management (connect, reconnect, close)
- Integration with Claude, Cursor IDE, and other MCP-compatible clients
- Convert natural language to SQL using semantic understanding
- Handle query results and format them for easy reading
- Secure database operations with proper authentication

## Prerequisites

- Python 3.8+
- Snowflake account with appropriate access permissions
- MCP-compatible client (Claude, Cursor IDE, etc.)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/snowflake-mcp.git
cd snowflake-mcp
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the sample environment file and add your Snowflake credentials:

```bash
cp .env.sample .env
# Edit .env with your Snowflake credentials
```

## Configuration

### Environment Variables

Create a `.env` file with your Snowflake credentials:

```
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account_locator  # e.g., xy12345.us-east-2
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_SCHEMA=your_schema  # Optional, defaults to PUBLIC
SNOWFLAKE_ROLE=your_role  # Optional, defaults to user's default role
```

### MCP Client Configuration

#### For Cursor IDE:

Cursor automatically discovers and integrates with MCP servers. Just make sure the server is running.

#### For Claude Desktop:

Add the following to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "snowflake": {
      "command": "/path/to/python",
      "args": ["/path/to/snowflake-mcp/src/server.py"]
    }
  }
}
```

Replace `/path/to/python` with the path to your Python interpreter, and `/path/to/snowflake-mcp` with the full path to where you cloned this repository.

## Usage

The Snowflake MCP server implements the Model Context Protocol (MCP) specification, allowing AI systems like Claude to connect to Snowflake databases through natural language.

### Using MCP CLI (Recommended)

The MCP Python SDK includes a command-line interface that makes it easy to run and manage MCP servers:

1. **Development Mode with Inspector UI**:

```bash
mcp dev src/server.py
```

This starts the server and opens an inspector interface in your browser where you can test the tools.

2. **Install in Claude Desktop**:

```bash
mcp install src/server.py
```

This installs the server in Claude Desktop, making it available for Claude to use.

3. **Standard Mode**:

```bash
mcp run src/server.py
```

This runs the server in standard mode without the inspector interface.

### Available Tools

The Snowflake MCP server provides the following tools:

1. **query_database** - Execute SQL or natural language queries on Snowflake
2. **list_tables** - List all tables in the database
3. **get_table_schema** - Get the schema of a specific table

For more examples and detailed parameter information, check the [examples/README.md](examples/README.md) file.

### Running Manually

You can also run the server directly, which is useful for debugging:

```bash
python src/server.py
```

This starts the server in standalone mode using stdio transport.

## Deployment

### Hosting on Smithery

This server can be hosted on Smithery.ai for easy access by other users:

1. Create an account on [Smithery.ai](https://smithery.ai)
2. Add your server to the Smithery registry
3. Configure deployment using the Dockerfile in this repository
4. Click "Deploy" on the Deployments tab on your server page

The Dockerfile is already configured to properly build and run the server with WebSocket transport support for Smithery hosting.

### Security Considerations

When hosting your Snowflake MCP server publicly:

- Consider using a read-only Snowflake account
- Restrict access to specific schemas/tables
- Use environment variables for secure credential management

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -m 'Add new feature'`
6. Push to the branch: `git push origin feature/new-feature`
7. Submit a pull request

## License

MIT License

## Acknowledgements

- The [Model Context Protocol](https://modelcontextprotocol.io/) team for creating the standard
- Snowflake for their robust database and API
