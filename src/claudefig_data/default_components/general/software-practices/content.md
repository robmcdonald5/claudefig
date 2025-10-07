## General Software Practices

### Code Quality Principles

**SOLID Principles:**
- **S**ingle Responsibility: Each class/function has one clear purpose
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Subtypes must be substitutable for base types
- **I**nterface Segregation: Many specific interfaces over one general interface
- **D**ependency Inversion: Depend on abstractions, not concretions

**Additional Principles:**
- **DRY (Don't Repeat Yourself)**: Extract common logic into reusable components
- **KISS (Keep It Simple, Stupid)**: Simple solutions are more maintainable
- **YAGNI (You Aren't Gonna Need It)**: Don't build features before they're needed
- **Separation of Concerns**: Divide program into distinct sections, each addressing a separate concern

### Code Organization

- **Consistent naming**: Use clear, descriptive names (avoid abbreviations unless common)
- **Small functions**: Functions should do one thing and do it well (< 50 lines ideal)
- **Deep modules**: Prefer deep, well-encapsulated modules over shallow ones
- **File structure**: Organize by feature/domain, not by type

### Error Handling

- **Fail fast**: Detect and report errors as early as possible
- **Specific exceptions**: Use specific exception types, not generic ones
- **Clean error messages**: Provide context and actionable information
- **Don't swallow exceptions**: Log or re-raise, never silent catch-all

### Performance

- **Profile before optimizing**: Measure actual bottlenecks, don't guess
- **Optimize the right things**: Focus on algorithmic complexity over micro-optimizations
- **Cache wisely**: Only cache when measurably beneficial
- **Consider scalability**: Think about how code performs with 10x, 100x, 1000x data
