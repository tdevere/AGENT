# Project Name

A brief description of your Python project.

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd AGENT

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```python
# Example usage
python main.py
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linting
flake8 src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Docker Usage

Build and start the server using Docker Compose:

```bash
docker compose up -d --build
# import bible texts
docker compose exec api bundle exec ruby import.rb
```

Verify the API:

```bash
curl http://localhost:4567/John+3:16
```

### Command Line Client

The Python client provides access to all API endpoints:

```bash
# List translations
python client/client.py translations --server http://localhost:4567
```

Use `--help` for complete command options.
