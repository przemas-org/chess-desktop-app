# Chess Desktop App

A chess desktop application built with Python. The application is designed for one human player to play a game with bot player.

## Features

- Basic chess application framework
- Modular project structure
- Ready for expansion

## Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)

## Installation

1. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository and navigate to the project directory:
```bash
cd chess_desktop_app
```

3. Install dependencies:
```bash
poetry install
```

## Usage

Run the application using Poetry:
```bash
poetry run chess-app
```

Or activate the virtual environment and run directly:
```bash
poetry shell
python -m chess_app.main
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Running Tests with Coverage

```bash
poetry run pytest --cov=chess_app
```

### Adding Dependencies

```bash
poetry add <package-name>
```

### Adding Development Dependencies

```bash
poetry add --group dev <package-name>
```

## Project Structure

```
chess_desktop_app/
├── pyproject.toml          # Poetry configuration
├── README.md               # This file
├── chess_app/              # Main package
│   ├── __init__.py
│   └── main.py             # Entry point
└── tests/                  # Test directory
    └── __init__.py
```

## License

MIT

## Author

Your Name
