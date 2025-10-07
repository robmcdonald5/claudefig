"""Tests for renderer.py - ComponentRenderer and MarkdownComposer."""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import TemplateSyntaxError

from claudefig.renderer import ComponentRenderer, MarkdownComposer


class TestComponentRenderer:
    """Test ComponentRenderer class."""

    @pytest.fixture
    def renderer(self):
        """Create ComponentRenderer instance."""
        return ComponentRenderer()

    def test_render_simple_string(self, renderer):
        """Test rendering a simple string template."""
        template = "Hello, {{ name }}!"
        variables = {"name": "World"}

        result = renderer.render_string(template, variables)

        assert result == "Hello, World!"

    def test_render_with_multiple_variables(self, renderer):
        """Test rendering with multiple variables."""
        template = "{{ greeting }}, {{ name }}! You are {{ age }} years old."
        variables = {
            "greeting": "Hello",
            "name": "Alice",
            "age": 30,
        }

        result = renderer.render_string(template, variables)

        assert result == "Hello, Alice! You are 30 years old."

    def test_render_with_conditional(self, renderer):
        """Test rendering with Jinja2 conditionals."""
        template = "{% if enabled %}Feature is enabled{% else %}Feature is disabled{% endif %}"

        result_enabled = renderer.render_string(template, {"enabled": True})
        result_disabled = renderer.render_string(template, {"enabled": False})

        assert result_enabled == "Feature is enabled"
        assert result_disabled == "Feature is disabled"

    def test_render_with_loop(self, renderer):
        """Test rendering with Jinja2 loops."""
        template = "{% for item in items %}- {{ item }}\n{% endfor %}"
        variables = {"items": ["apple", "banana", "cherry"]}

        result = renderer.render_string(template, variables)

        assert result == "- apple\n- banana\n- cherry\n"

    def test_render_file_success(self, renderer, tmp_path):
        """Test rendering a file successfully."""
        # Create a test template file
        template_file = tmp_path / "template.md"
        template_file.write_text("# {{ title }}\n\n{{ content }}", encoding="utf-8")

        variables = {
            "title": "Test Document",
            "content": "This is test content."
        }

        result = renderer.render_file(template_file, variables)

        assert result == "# Test Document\n\nThis is test content."

    def test_render_file_not_found(self, renderer, tmp_path):
        """Test that rendering non-existent file raises FileNotFoundError."""
        non_existent = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError, match="Component file not found"):
            renderer.render_file(non_existent, {})

    def test_render_invalid_jinja2_syntax(self, renderer):
        """Test that invalid Jinja2 syntax raises exception."""
        invalid_template = "{{ unclosed"

        with pytest.raises(Exception):
            renderer.render_string(invalid_template, {})

    def test_render_component_files_single(self, renderer, tmp_path):
        """Test rendering single component file."""
        file1 = tmp_path / "content.md"
        file1.write_text("# {{ title }}", encoding="utf-8")

        result = renderer.render_component_files(
            [file1],
            {"title": "Component 1"}
        )

        assert result == "# Component 1"

    def test_render_component_files_multiple(self, renderer, tmp_path):
        """Test rendering multiple component files concatenated."""
        file1 = tmp_path / "file1.md"
        file1.write_text("# {{ title1 }}", encoding="utf-8")

        file2 = tmp_path / "file2.md"
        file2.write_text("## {{ title2 }}", encoding="utf-8")

        result = renderer.render_component_files(
            [file1, file2],
            {"title1": "First", "title2": "Second"}
        )

        assert result == "# First\n\n## Second"

    def test_render_component_files_with_failure(self, renderer, tmp_path, capsys):
        """Test that render_component_files continues on error and warns."""
        file1 = tmp_path / "file1.md"
        file1.write_text("# Content 1", encoding="utf-8")

        file2 = tmp_path / "nonexistent.md"  # This will fail

        file3 = tmp_path / "file3.md"
        file3.write_text("# Content 3", encoding="utf-8")

        result = renderer.render_component_files([file1, file2, file3], {})

        # Should render file1 and file3, skip file2
        assert result == "# Content 1\n\n# Content 3"

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning: Skipping" in captured.out


class TestMarkdownComposer:
    """Test MarkdownComposer class."""

    @pytest.fixture
    def composer(self):
        """Create MarkdownComposer instance."""
        return MarkdownComposer()

    def test_add_single_section(self, composer):
        """Test adding a single section."""
        composer.add_section("Introduction", "# Introduction\n\nWelcome!", 10)

        assert composer.has_section("Introduction")
        assert composer.get_section_content("Introduction") == "# Introduction\n\nWelcome!"

    def test_add_multiple_sections(self, composer):
        """Test adding multiple sections."""
        composer.add_section("Section 1", "Content 1", 10)
        composer.add_section("Section 2", "Content 2", 20)
        composer.add_section("Section 3", "Content 3", 30)

        assert composer.has_section("Section 1")
        assert composer.has_section("Section 2")
        assert composer.has_section("Section 3")

    def test_add_duplicate_section_lower_priority(self, composer):
        """Test that duplicate section with lower priority replaces existing."""
        composer.add_section("Test", "Original content", 20)
        composer.add_section("Test", "New content", 10)  # Lower priority

        # Should use the new content with lower priority
        content = composer.get_section_content("Test")
        assert content == "New content"

    def test_add_duplicate_section_higher_priority(self, composer):
        """Test that duplicate section with higher priority is ignored."""
        composer.add_section("Test", "Original content", 10)
        composer.add_section("Test", "New content", 20)  # Higher priority

        # Should keep the original content with lower priority
        content = composer.get_section_content("Test")
        assert content == "Original content"

    def test_compose_empty(self, composer):
        """Test composing with no sections returns empty string."""
        result = composer.compose()
        assert result == ""

    def test_compose_single_section(self, composer):
        """Test composing a single section."""
        composer.add_section("Test", "# Test\n\nContent", 10)

        result = composer.compose()

        assert result == "# Test\n\nContent"

    def test_compose_multiple_sections_ordered(self, composer):
        """Test that sections are composed in priority order."""
        composer.add_section("Third", "# Third", 30)
        composer.add_section("First", "# First", 10)
        composer.add_section("Second", "# Second", 20)

        result = composer.compose()

        # Should be ordered by priority (10, 20, 30)
        assert result == "# First\n\n# Second\n\n# Third"

    def test_compose_with_toc(self, composer):
        """Test composing with table of contents."""
        composer.add_section("Introduction", "# Introduction\n\nWelcome!", 10)
        composer.add_section("Getting Started", "# Getting Started\n\nLet's begin.", 20)

        result = composer.compose(include_toc=True)

        # Should have TOC at top
        assert "# Table of Contents" in result
        assert "- [Introduction](#introduction)" in result
        assert "- [Getting Started](#getting-started)" in result
        assert "---" in result  # Separator
        assert "# Introduction" in result
        assert "# Getting Started" in result

    def test_get_section_content_not_found(self, composer):
        """Test getting content for non-existent section returns empty string."""
        content = composer.get_section_content("NonExistent")
        assert content == ""

    def test_has_section_false(self, composer):
        """Test has_section returns False for non-existent section."""
        assert not composer.has_section("NonExistent")

    def test_clear(self, composer):
        """Test clearing all sections."""
        composer.add_section("Section 1", "Content 1", 10)
        composer.add_section("Section 2", "Content 2", 20)

        assert composer.has_section("Section 1")
        assert composer.has_section("Section 2")

        composer.clear()

        assert not composer.has_section("Section 1")
        assert not composer.has_section("Section 2")
        assert composer.compose() == ""

    def test_toc_anchor_generation(self, composer):
        """Test that TOC anchors are generated correctly."""
        composer.add_section("Python Coding Standards", "# Python Coding Standards", 10)
        composer.add_section("Git Workflow", "# Git Workflow", 20)

        result = composer.compose(include_toc=True)

        # Anchors should be lowercase with hyphens
        assert "[Python Coding Standards](#python-coding-standards)" in result
        assert "[Git Workflow](#git-workflow)" in result

    def test_priority_default_value(self, composer):
        """Test that default priority is 100."""
        composer.add_section("Default Priority", "Content with default priority")
        composer.add_section("Lower Priority", "Content with priority 50", 50)

        result = composer.compose()

        # Lower priority (50) should come first
        lines = result.split("\n\n")
        assert "Content with priority 50" in lines[0]
        assert "Content with default priority" in lines[1]
