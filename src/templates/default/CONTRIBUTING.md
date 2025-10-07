# Contributing Guidelines

Thank you for considering contributing to this project!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Run tests and linting
6. Submit a pull request

## Development Setup

```bash
# Clone the repository
git clone <your-fork-url>
cd <project-name>

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting and formatting check
ruff check .
ruff format --check .
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Write docstrings for all public functions and classes
- Keep functions focused and concise
- Add tests for new features

## Commit Messages

Write clear, descriptive commit messages:
- Use present tense ("Add feature" not "Added feature")
- Keep first line under 50 characters
- Provide details in the body if needed

## Pull Request Process

1. Update documentation if needed
2. Ensure all tests pass
3. Update CHANGELOG.md if applicable
4. Request review from maintainers
5. Address any feedback promptly

## Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages or logs if applicable

## Questions?

Feel free to open an issue for questions or discussions.
