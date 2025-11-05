"""Tests for FileTemplateManager class."""

from pathlib import Path
from unittest.mock import patch

import pytest

from claudefig.template_manager import FileTemplateManager


class TestTemplateManagerInit:
    """Tests for FileTemplateManager.__init__ method."""

    def test_init_without_custom_dir(self):
        """Test initialization without custom template directory."""
        manager = FileTemplateManager()

        assert manager.custom_template_dir is None

    def test_init_with_custom_dir(self, tmp_path):
        """Test initialization with custom template directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        assert manager.custom_template_dir == custom_dir


class TestGetTemplateDir:
    """Tests for FileTemplateManager.get_template_dir method."""

    def test_get_builtin_template(self):
        """Test getting built-in template directory."""
        manager = FileTemplateManager()

        # Should not raise an error for default template
        template_dir = manager.get_template_dir("default")

        assert template_dir is not None
        assert isinstance(template_dir, Path)

    def test_get_custom_template_exists(self, tmp_path):
        """Test getting custom template when it exists."""
        # Create custom template directory structure
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        my_template = custom_dir / "my_template"
        my_template.mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        # Should return the custom template path
        result = manager.get_template_dir("my_template")

        assert result == my_template

    def test_custom_template_doesnt_exist_fallback_to_builtin(self, tmp_path):
        """Test fallback to built-in template when custom doesn't exist."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        # Should fall back to built-in template
        result = manager.get_template_dir("default")

        assert result is not None
        # Should be the built-in path, not the custom dir
        assert "custom_templates" not in str(result)

    def test_builtin_template_returns_path_even_if_not_exists(self):
        """Test that get_template_dir returns a path even if template doesn't exist.

        Note: Validation happens later when trying to read files from the path,
        not when getting the template directory path.
        """
        manager = FileTemplateManager()

        # get_template_dir doesn't validate existence, just returns a path
        result = manager.get_template_dir("nonexistent_template")

        # Should return a Path object
        assert isinstance(result, Path)
        # The path probably doesn't exist
        # (actual existence check happens when trying to use the template)

    def test_custom_template_preferred_over_builtin(self, tmp_path):
        """Test that custom template is preferred over built-in with same name."""
        # Create custom template with same name as built-in
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        default_template = custom_dir / "default"
        default_template.mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        # Should return custom template, not built-in
        result = manager.get_template_dir("default")

        assert result == default_template


class TestListTemplates:
    """Tests for FileTemplateManager.list_templates method."""

    def test_list_builtin_templates(self):
        """Test listing built-in templates."""
        manager = FileTemplateManager()

        templates = manager.list_templates()

        # Should return a list (might be empty if templates aren't accessible in dev mode)
        assert isinstance(templates, list)
        # If templates are accessible, should include 'default'
        # In dev mode without proper packaging, this might be empty - that's ok

    def test_list_custom_templates(self, tmp_path):
        """Test listing custom templates."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        # Create some custom templates
        (custom_dir / "custom1").mkdir()
        (custom_dir / "custom2").mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        templates = manager.list_templates()

        # Should include custom templates (marked with "(custom)")
        assert "custom1 (custom)" in templates
        assert "custom2 (custom)" in templates

    def test_list_mixed_builtin_and_custom(self, tmp_path):
        """Test listing both built-in and custom templates."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        (custom_dir / "my_custom").mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        templates = manager.list_templates()

        # Should have both built-in and custom
        assert len(templates) > 0
        # Should have at least one custom template
        assert any("(custom)" in t for t in templates)

    def test_list_when_custom_dir_doesnt_exist(self, tmp_path):
        """Test listing templates when custom directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"

        manager = FileTemplateManager(custom_template_dir=nonexistent_dir)

        templates = manager.list_templates()

        # Should not crash and should return a list
        # Built-in templates may or may not be accessible depending on packaging
        assert isinstance(templates, list)

    def test_excludes_hidden_directories(self, tmp_path):
        """Test that hidden directories (starting with _) are excluded."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        # Create templates including hidden ones
        (custom_dir / "visible_template").mkdir()
        (custom_dir / "_hidden_template").mkdir()
        (custom_dir / "__pycache__").mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        templates = manager.list_templates()

        # Should include visible template
        assert "visible_template (custom)" in templates
        # Should NOT include hidden templates
        assert not any("_hidden" in t for t in templates)
        assert not any("__pycache__" in t for t in templates)

    def test_list_templates_sorted(self, tmp_path):
        """Test that templates are returned in sorted order."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        # Create templates in non-alphabetical order
        (custom_dir / "zebra").mkdir()
        (custom_dir / "alpha").mkdir()
        (custom_dir / "beta").mkdir()

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        templates = manager.list_templates()

        # Extract just the custom template names
        custom_templates = [
            t.replace(" (custom)", "") for t in templates if "(custom)" in t
        ]

        # Should be sorted
        assert custom_templates == sorted(custom_templates)


class TestGetTemplateFiles:
    """Tests for FileTemplateManager.get_template_files method."""

    def test_get_files_from_existing_template(self):
        """Test getting files from an existing template."""
        manager = FileTemplateManager()

        # Get files from default template
        files = manager.get_template_files("default")

        # Should return a list
        assert isinstance(files, list)
        # Default template should have some files
        assert len(files) > 0
        # All should be Path objects
        assert all(isinstance(f, Path) for f in files)

    def test_get_files_from_nonexistent_template(self):
        """Test getting files from non-existent template returns empty list."""
        manager = FileTemplateManager()

        # Mock get_template_dir to return a path that doesn't exist
        with patch.object(
            manager,
            "get_template_dir",
            return_value=Path("/nonexistent/template/path"),
        ):
            files = manager.get_template_files("fake")

            # Should return empty list, not raise error
            assert files == []

    def test_excludes_hidden_files(self, tmp_path):
        """Test that hidden files (starting with _) are excluded."""
        # Create custom template with files
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        template_dir = custom_dir / "test_template"
        template_dir.mkdir()

        # Create files including hidden ones
        (template_dir / "visible.md").write_text("content", encoding="utf-8")
        (template_dir / "_hidden.md").write_text("content", encoding="utf-8")
        (template_dir / ".gitignore").write_text("content", encoding="utf-8")

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        files = manager.get_template_files("test_template")

        # Should only include visible file
        file_names = [f.name for f in files]
        assert "visible.md" in file_names
        assert "_hidden.md" not in file_names
        # Note: .gitignore starts with . not _, so it might be included

    def test_only_returns_files_not_directories(self, tmp_path):
        """Test that only files are returned, not subdirectories."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        template_dir = custom_dir / "test_template"
        template_dir.mkdir()

        # Create both files and subdirectories
        (template_dir / "file.md").write_text("content", encoding="utf-8")
        (template_dir / "subdir").mkdir()
        (template_dir / "another_file.txt").write_text("content", encoding="utf-8")

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        files = manager.get_template_files("test_template")

        # Should only include files
        file_names = [f.name for f in files]
        assert "file.md" in file_names
        assert "another_file.txt" in file_names
        assert "subdir" not in file_names


class TestReadTemplateFile:
    """Tests for FileTemplateManager.read_template_file method."""

    def test_read_existing_file(self):
        """Test reading an existing template file."""
        manager = FileTemplateManager()

        # Read a file from default template (claudefig.toml should exist)
        content = manager.read_template_file("default", "claudefig.toml")

        # Should return string content
        assert isinstance(content, str)
        assert len(content) > 0
        # Verify it's a valid preset configuration file
        assert "[preset]" in content or "[claudefig]" in content

    def test_read_nonexistent_file_raises(self):
        """Test that reading non-existent file raises FileNotFoundError."""
        manager = FileTemplateManager()

        with pytest.raises(FileNotFoundError, match="not found"):
            manager.read_template_file("default", "nonexistent_file_xyz.md")

    def test_read_file_encoding(self, tmp_path):
        """Test that files are read with UTF-8 encoding."""
        # Create custom template with UTF-8 content
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        template_dir = custom_dir / "test_template"
        template_dir.mkdir()

        # Write file with special characters
        test_file = template_dir / "test.md"
        expected_content = "# Test File\n\nThis has émojis 🎉 and spëcial chars"
        test_file.write_text(expected_content, encoding="utf-8")

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        # Read the file
        content = manager.read_template_file("test_template", "test.md")

        # Should preserve UTF-8 characters
        assert content == expected_content

    def test_read_file_from_custom_template(self, tmp_path):
        """Test reading file from custom template directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        template_dir = custom_dir / "my_template"
        template_dir.mkdir()

        # Create a test file
        test_file = template_dir / "custom.md"
        expected_content = "# Custom Template Content"
        test_file.write_text(expected_content, encoding="utf-8")

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        content = manager.read_template_file("my_template", "custom.md")

        assert content == expected_content

    def test_read_file_with_nested_path(self, tmp_path):
        """Test reading file with path like 'claude/settings.json'."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        template_dir = custom_dir / "test_template"
        template_dir.mkdir()

        # Create nested directory structure
        subdir = template_dir / "claude"
        subdir.mkdir()
        test_file = subdir / "settings.json"
        expected_content = '{"key": "value"}'
        test_file.write_text(expected_content, encoding="utf-8")

        manager = FileTemplateManager(custom_template_dir=custom_dir)

        # Read using nested path
        content = manager.read_template_file("test_template", "claude/settings.json")

        assert content == expected_content
