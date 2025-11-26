"""Property-based tests for claudefig using Hypothesis.

These tests verify invariants and edge cases that would be difficult
to cover with example-based testing alone.
"""

from __future__ import annotations

import string

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from claudefig.models import FileType
from claudefig.services import file_instance_service
from tests.factories import FileInstanceFactory


class TestGenerateInstanceIdProperties:
    """Property-based tests for generate_instance_id()."""

    @given(
        preset_name=st.text(
            alphabet=string.ascii_lowercase + string.digits + "-_",
            min_size=1,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_generated_id_is_non_empty(self, preset_name):
        """Generated IDs are never empty."""
        assume(preset_name.strip())  # Skip empty-ish names

        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD, preset_name, None, {}
        )

        assert result
        assert len(result) > 0

    @given(
        preset_name=st.text(
            alphabet=string.ascii_lowercase + string.digits,
            min_size=1,
            max_size=20,
        ),
    )
    @settings(max_examples=100)
    def test_generated_id_contains_file_type(self, preset_name):
        """Generated IDs always contain the file type."""
        assume(preset_name.strip())

        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD, preset_name, None, {}
        )

        assert FileType.CLAUDE_MD.value in result

    @given(
        preset_name=st.text(
            alphabet=string.ascii_lowercase,
            min_size=1,
            max_size=10,
        ),
        num_existing=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=50)
    def test_generated_id_is_unique(self, preset_name, num_existing):
        """Generated IDs are always unique relative to existing instances."""
        assume(preset_name.strip())

        # Build existing instances dict
        existing = {}
        base_id = f"{FileType.CLAUDE_MD.value}-{preset_name}"

        # Add base ID
        if num_existing > 0:
            existing[base_id] = FileInstanceFactory(id=base_id)

        # Add numbered IDs
        for i in range(1, num_existing):
            numbered_id = f"{base_id}-{i}"
            existing[numbered_id] = FileInstanceFactory(id=numbered_id)

        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD, preset_name, None, existing
        )

        assert result not in existing


class TestValidatePathProperties:
    """Property-based tests for validate_path()."""

    @given(
        path=st.text(min_size=1, max_size=100).filter(
            lambda p: ".." not in p and not p.startswith("/")
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_relative_paths_without_traversal_dont_error_on_traversal(
        self, tmp_path, path
    ):
        """Paths without .. never fail with 'parent directory' error."""
        assume(path.strip())
        # Skip paths with invalid characters for file systems
        assume(not any(c in path for c in ["<", ">", ":", '"', "|", "?", "*", "\x00"]))

        result = file_instance_service.validate_path(path, FileType.CLAUDE_MD, tmp_path)

        # Should not have parent directory error (may have other errors)
        for error in result.errors:
            assert "parent directory" not in error.lower()

    @given(
        num_dots=st.integers(min_value=1, max_value=5),
        suffix=st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10),
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_parent_traversal_always_rejected(self, tmp_path, num_dots, suffix):
        """Any path with ../ is always rejected."""
        path = "../" * num_dots + suffix + ".md"

        result = file_instance_service.validate_path(path, FileType.CLAUDE_MD, tmp_path)

        assert not result.valid
        assert any("parent directory" in e for e in result.errors)


class TestFileTypeProperties:
    """Property-based tests for FileType enum."""

    @given(file_type=st.sampled_from(list(FileType)))
    def test_all_file_types_have_display_name(self, file_type):
        """All FileType values have a non-empty display name."""
        assert file_type.display_name
        assert isinstance(file_type.display_name, str)
        assert len(file_type.display_name) > 0

    @given(file_type=st.sampled_from(list(FileType)))
    def test_all_file_types_have_default_path(self, file_type):
        """All FileType values have a default path."""
        assert file_type.default_path
        assert isinstance(file_type.default_path, str)
