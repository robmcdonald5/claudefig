## Python Coding Standards

**Python Version:** {{ python_version }}+

### Code Style and Formatting

**Primary Tool:** Ruff (combines formatting + linting)

- **Formatter**: Ruff format
- **Linter**: Ruff check (replaces Flake8, isort, pyupgrade)
- **Configuration**: `pyproject.toml` → `[tool.ruff]`
- **Line length**: 88 characters
- **Target version**: py{{ python_version | replace(".", "") }}

**Key Rules:**
- Run `ruff format` before committing
- Run `ruff check --fix` to auto-fix linting issues
- Configure in `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 88
  target-version = "py{{ python_version | replace(".", "") }}"

  [tool.ruff.lint]
  select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM"]
  ```

### Type Hints

{% if use_mypy %}
**Type Checker:** mypy (strict mode)

- **Required**: All public functions and methods must have type hints
- **Configuration**: `pyproject.toml` → `[tool.mypy]`
- **Strict mode**: Enabled for maximum type safety

**Example:**
```python
def calculate_total(items: list[Item], tax_rate: float) -> Decimal:
    """Calculate total price with tax."""
    subtotal = sum(item.price for item in items)
    return Decimal(subtotal * (1 + tax_rate))
```

**Type Hint Rules:**
- Use built-in generics (`list[str]`, not `List[str]`) for Python {{ python_version }}+
- Use `Optional[T]` or `T | None` for nullable values
- Use `Any` sparingly - prefer specific types
- Use `Protocol` for structural subtyping
{% else %}
**Type Hints:** Optional but encouraged

- Use type hints for public APIs
- Consider gradual typing approach
- Document complex types in docstrings
{% endif %}

### Docstrings

**Format:** Google-style docstrings

**Required for:**
- All public modules, classes, functions, and methods
- Complex private functions

**Example:**
```python
def process_payment(
    amount: Decimal,
    payment_method: PaymentMethod,
    customer: Customer
) -> PaymentResult:
    """Process a customer payment transaction.

    Args:
        amount: Payment amount in USD.
        payment_method: Method of payment (card, bank, etc.).
        customer: Customer making the payment.

    Returns:
        PaymentResult with transaction ID and status.

    Raises:
        InsufficientFundsError: If customer has insufficient funds.
        InvalidPaymentMethodError: If payment method is invalid or expired.

    Example:
        >>> result = process_payment(
        ...     Decimal("99.99"),
        ...     PaymentMethod.CREDIT_CARD,
        ...     customer
        ... )
        >>> assert result.status == PaymentStatus.SUCCESS
    """
```

### Testing

{% if use_pytest %}
**Testing Framework:** pytest

**Requirements:**
- Minimum coverage: 85%
- Test file naming: `test_*.py` or `*_test.py`
- Test function naming: `test_<what>_<condition>_<expected>()`
- Use fixtures for reusable test setup
- Use parametrize for testing multiple inputs

**Example:**
```python
import pytest
from decimal import Decimal

@pytest.fixture
def sample_items():
    return [
        Item(name="Widget", price=Decimal("10.00")),
        Item(name="Gadget", price=Decimal("20.00")),
    ]

def test_calculate_total_with_no_tax_returns_subtotal(sample_items):
    result = calculate_total(sample_items, tax_rate=0.0)
    assert result == Decimal("30.00")

@pytest.mark.parametrize("tax_rate,expected", [
    (0.0, Decimal("30.00")),
    (0.1, Decimal("33.00")),
    (0.2, Decimal("36.00")),
])
def test_calculate_total_with_various_tax_rates(sample_items, tax_rate, expected):
    result = calculate_total(sample_items, tax_rate)
    assert result == expected
```
{% else %}
**Testing Framework:** unittest or pytest

- Write tests for all public APIs
- Aim for high test coverage (> 80%)
- Use mocks for external dependencies
{% endif %}

### Project Structure

```
project/
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── module.py
│       └── subpackage/
├── tests/
│   ├── __init__.py
│   └── test_module.py
├── docs/
├── pyproject.toml
├── README.md
└── .gitignore
```

### Dependencies

- **Manage with**: `pyproject.toml` (PEP 621)
- **Pin versions**: Use exact versions in production, ranges in libraries
- **Virtual environments**: Always use venv or similar
- **Lock files**: Use `pip-compile` or `poetry.lock` for reproducible builds

### Code Quality Checklist

Before committing Python code:

- [ ] Run `ruff format .` to format code
- [ ] Run `ruff check --fix .` to fix linting issues
{% if use_mypy %}
- [ ] Run `mypy .` to check types
{% endif %}
{% if use_pytest %}
- [ ] Run `pytest` and ensure all tests pass
- [ ] Check coverage with `pytest --cov`
{% endif %}
- [ ] Update docstrings for any changed public APIs
- [ ] Add tests for new functionality
