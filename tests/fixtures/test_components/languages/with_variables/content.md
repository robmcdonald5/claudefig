# {{ project_name }} Configuration

## Language Settings
- Language Version: {{ language_version }}
- Strict Mode: {% if use_strict_mode %}Enabled{% else %}Disabled{% endif %}
- Max Line Length: {{ max_line_length }}

## Code Quality Standards
{% if use_strict_mode %}
All code must pass strict type checking and linting rules.
{% else %}
Standard code quality checks apply.
{% endif %}

## Project: {{ project_name }}
This project uses version {{ language_version }} with a maximum line length of {{ max_line_length }} characters.
