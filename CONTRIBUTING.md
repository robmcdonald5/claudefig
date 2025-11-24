# Contributing to claudefig

Thank you for your interest in contributing to claudefig! We welcome contributions from the community and are grateful for any help you can provide.

## Table of Contents

- [Types of Contributions](#types-of-contributions)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code of Conduct](#code-of-conduct)

## Types of Contributions

We welcome many types of contributions:

- **Bug Reports**: Found a bug? Let us know!
- **Platform Parity**: claudefig not working within your terminal or OS environement? Open an issue or a PR if you have the fix.

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/your-username/claudefig.git
cd claudefig
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/robmcdonald5/claudefig.git
```

### Development Environment Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

4. Verify the installation:

```bash
claudefig --version
pytest
```

## Development Workflow

```bash
git switch -c {change-type}/{change-description}
```

### Making Changes

1. Make your changes in your feature branch
2. Write or update tests as needed
3. Do not update any existing documentation, let your PR speak for itself
4. Run linters and formatters (pre-commit will do this automatically on commit)

### Running Tests Locally

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claudefig --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Running Linters and Formatters

Pre-commit hooks will run automatically, but you can also run them manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run Ruff linter
ruff check src/ tests/

# Run Ruff formatter
ruff format src/ tests/

# Run mypy type checker
mypy src/
```

## Code Style Guidelines

### Python Style

- **Formatter**: Ruff format (line length: 88 characters)
- **Linter**: Ruff
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings

### Docstring Format

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of function.

    More detailed description if needed. Explain what the function does,
    not how it does it.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param2 is negative.

    Example:
        >>> example_function("test", 5)
        True
    """
    pass
```

### Import Order

Imports should be organized in the following order (handled by Ruff):

1. Standard library imports
2. Third-party imports
3. Local application imports

### Naming Conventions

- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods/variables**: `_leading_underscore`

## Testing Guidelines

### Writing Tests

- Use pytest for all tests
- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names

Example:

```python
def test_init_command_creates_config_file():
    """Test that init command creates a configuration file."""
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(cli, ['init'])

    # Assert
    assert result.exit_code == 0
    assert "Configuration created" in result.output
```

### Testing CLI Applications

Use Click's `CliRunner` for testing CLI commands:

```python
from click.testing import CliRunner
from claudefig.cli import cli

def test_help_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output
```

### Coverage Requirements

- Any new code needs to have **100%** coverage of any methods/functions that interact with the TUI or CLI
- Run coverage reports: `pytest --cov=claudefig --cov-report=html`
- View report: open `htmlcov/index.html` in a browser

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines (formatted with Ruff)
- [ ] Tests pass locally (`pytest`)
- [ ] New tests added for any new methods/functions
- [ ] Commits are clean and well-described

### Submitting a Pull Request

1. Push your branch to your fork:

```bash
git push origin feature/your-feature-name
```

2. Go to GitHub and create a pull request

3. Fill out the PR template with:
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Screenshots (if applicable)

4. Wait for review and address feedback

## Questions?

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Email**: For private inquiries
