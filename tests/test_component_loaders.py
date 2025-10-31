"""Tests for component loading using Chain of Responsibility pattern."""

from pathlib import Path
from unittest.mock import Mock, patch

from claudefig.component_loaders import (
    ComponentLoader,
    GlobalComponentLoader,
    PresetComponentLoader,
    create_component_loader_chain,
)


class TestComponentLoaderBase:
    """Tests for base ComponentLoader class."""

    def test_loader_delegates_to_next_when_not_found(self):
        """Test that loader delegates to next loader when component not found."""
        # Create a mock loader that always returns None
        first_loader = Mock(spec=ComponentLoader)
        first_loader.try_load.return_value = None

        # Create a mock next loader that returns a path
        next_loader = Mock(spec=ComponentLoader)
        expected_path = Path("/mock/path")
        next_loader.load.return_value = expected_path

        first_loader.next_loader = next_loader
        first_loader.load = ComponentLoader.load.__get__(first_loader, ComponentLoader)

        # Load should delegate to next loader
        result = first_loader.load("default", "claude_md", "test")
        assert result == expected_path
        next_loader.load.assert_called_once_with("default", "claude_md", "test")

    def test_loader_returns_none_when_no_next_loader(self):
        """Test that loader returns None when no next loader exists."""
        loader = Mock(spec=ComponentLoader)
        loader.try_load.return_value = None
        loader.next_loader = None
        loader.load = ComponentLoader.load.__get__(loader, ComponentLoader)

        result = loader.load("default", "claude_md", "test")
        assert result is None


class TestPresetComponentLoader:
    """Tests for PresetComponentLoader."""

    @patch("claudefig.component_loaders.files")
    def test_loads_from_preset_specific_directory(self, mock_files):
        """Test loading component from preset-specific directory."""
        # Mock the path structure
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/mock/preset/components/claude_md/test")
        mock_path_obj = Path("/mock/preset/components/claude_md/test")

        mock_files.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_path

        loader = PresetComponentLoader()

        with (
            patch.object(Path, "exists", return_value=True),
            patch("claudefig.component_loaders.Path") as mock_path_class,
        ):
            mock_path_class.return_value = mock_path_obj
            result = loader.try_load("default", "claude_md", "test")

            assert result == mock_path_obj

    @patch("claudefig.component_loaders.files")
    def test_returns_none_when_preset_path_not_found(self, mock_files):
        """Test returns None when preset-specific path doesn't exist."""
        mock_files.side_effect = FileNotFoundError("Not found")

        loader = PresetComponentLoader()
        result = loader.try_load("default", "claude_md", "test")

        assert result is None


class TestGlobalComponentLoader:
    """Tests for GlobalComponentLoader."""

    @patch("claudefig.user_config.get_components_dir")
    def test_loads_from_global_pool(self, mock_get_components_dir):
        """Test loading component from global component pool."""
        mock_dir = Path("/home/user/.claudefig/components")
        mock_get_components_dir.return_value = mock_dir
        expected_path = mock_dir / "claude_md" / "test"

        loader = GlobalComponentLoader()

        with patch.object(Path, "exists", return_value=True):
            result = loader.try_load("default", "claude_md", "test")

            assert result == expected_path

    @patch("claudefig.user_config.get_components_dir")
    def test_returns_none_when_global_path_not_found(self, mock_get_components_dir):
        """Test returns None when global path doesn't exist."""
        mock_dir = Path("/home/user/.claudefig/components")
        mock_get_components_dir.return_value = mock_dir

        loader = GlobalComponentLoader()

        with patch.object(Path, "exists", return_value=False):
            result = loader.try_load("default", "claude_md", "test")

            assert result is None

    @patch("claudefig.user_config.get_components_dir")
    def test_returns_none_when_import_fails(self, mock_get_components_dir):
        """Test returns None when get_components_dir import fails."""
        mock_get_components_dir.side_effect = ImportError("Module not found")

        loader = GlobalComponentLoader()
        result = loader.try_load("default", "claude_md", "test")

        assert result is None


class TestComponentLoaderChain:
    """Tests for the complete loader chain."""

    def test_chain_creation_order(self):
        """Test that loader chain is created in correct priority order."""
        chain = create_component_loader_chain()

        # Verify chain structure
        assert isinstance(chain, PresetComponentLoader)
        assert isinstance(chain.next_loader, GlobalComponentLoader)
        assert chain.next_loader.next_loader is None

    @patch("claudefig.component_loaders.files")
    def test_chain_uses_preset_loader_first(self, mock_files):
        """Test that chain tries preset loader first."""
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/mock/preset/components/claude_md/test")
        mock_path_obj = Path("/mock/preset/components/claude_md/test")

        mock_files.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_path

        chain = create_component_loader_chain()

        with (
            patch.object(Path, "exists", return_value=True),
            patch("claudefig.component_loaders.Path") as mock_path_class,
        ):
            mock_path_class.return_value = mock_path_obj
            result = chain.load("default", "claude_md", "test")

            assert result == mock_path_obj

    @patch("claudefig.user_config.get_components_dir")
    @patch("claudefig.component_loaders.files")
    def test_chain_falls_back_to_global_when_preset_not_found(
        self, mock_files, mock_get_components_dir
    ):
        """Test that chain falls back to global loader when preset loader fails."""
        # Preset loader fails
        mock_files.side_effect = FileNotFoundError("Not found")

        # Global loader succeeds
        mock_dir = Path("/home/user/.claudefig/components")
        mock_get_components_dir.return_value = mock_dir
        expected_path = mock_dir / "claude_md" / "test"

        chain = create_component_loader_chain()

        with patch.object(Path, "exists", return_value=True):
            result = chain.load("default", "claude_md", "test")

            assert result == expected_path

    @patch("claudefig.component_loaders.files")
    @patch("claudefig.user_config.get_components_dir")
    def test_chain_returns_none_when_all_loaders_fail(
        self, mock_get_components_dir, mock_files
    ):
        """Test that chain returns None when all loaders fail."""
        # All loaders fail
        mock_files.side_effect = FileNotFoundError("Not found")
        mock_get_components_dir.side_effect = ImportError("Not found")

        chain = create_component_loader_chain()
        result = chain.load("default", "claude_md", "test")

        assert result is None
