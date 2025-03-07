FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install MCP SDK to ensure it's available
RUN pip install --no-cache-dir mcp==0.3.0

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/
COPY .env.sample .

# Create necessary log directories
RUN mkdir -p logs

# Make sure the server file is executable
RUN chmod +x src/server.py

# Set up for WebSocket transport
ENV MCP_TRANSPORT=websocket
ENV MCP_WEBSOCKET_PORT=8080
ENV MCP_WEBSOCKET_HOST=0.0.0.0

# Explicitly set Snowflake connection to lazy initialization
ENV SNOWFLAKE_LAZY_INIT=true

# Run server directly with Python
CMD ["python", "src/server.py"]

# Expose the port for WebSocket communication
EXPOSE 8080 