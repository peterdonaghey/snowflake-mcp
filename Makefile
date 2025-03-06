# Snowflake MCP Makefile
# Helper commands for development and running

.PHONY: install run example clean test lint

# Python executable
PYTHON := python

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Run the MCP server
run:
	$(PYTHON) src/server.py

# Run the example client
example:
	$(PYTHON) examples/simple_query.py

# Clean up build artifacts and logs
clean:
	rm -f snowflake_mcp.log
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf examples/__pycache__
	rm -rf .pytest_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Run tests
test:
	pytest

# Run linting
lint:
	flake8 src examples
	black --check src examples

# Format code
format:
	black src examples

# Create a .env file from the sample (if it doesn't exist)
.env:
	@if [ ! -f .env ]; then \
		cp .env.sample .env; \
		echo "Created .env file from .env.sample. Please edit with your credentials."; \
	else \
		echo ".env file already exists."; \
	fi

# Setup the project (install dependencies and create .env)
setup: install .env
	@echo "Setup complete. Remember to edit your .env file with Snowflake credentials."

# Help command
help:
	@echo "Snowflake MCP Makefile Commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run the MCP server"
	@echo "  make example    - Run the example client"
	@echo "  make clean      - Clean up build artifacts and logs"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting checks"
	@echo "  make format     - Format code using black"
	@echo "  make setup      - Set up the project (install dependencies and create .env)"
	@echo "  make help       - Show this help message" 