FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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

# Run server
CMD ["python", "src/server.py"]

# Expose the port for WebSocket communication
EXPOSE 8080 