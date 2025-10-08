"""Interactive TUI (Text User Interface) for claudefig."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Label, Static, Switch

from claudefig import __version__
from claudefig.config import Config


class SaveNotification(Static):
    """Notification widget for save confirmation."""

    def __init__(self, **kwargs) -> None:
        """Initialize notification."""
        super().__init__("Saved ✓", **kwargs)


class SettingItem(Container):
    """A single setting item with label, description, and switch."""

    def __init__(
        self,
        setting_key: str,
        label: str,
        description: str,
        initial_value: bool,
        **kwargs,
    ) -> None:
        """Initialize setting item.

        Args:
            setting_key: Config key (e.g., "init.create_claude_md")
            label: Display label
            description: Help text
            initial_value: Current setting value
        """
        super().__init__(**kwargs)
        self.setting_key = setting_key
        self.label_text = label
        self.description_text = description
        self.initial_value = initial_value

    def compose(self) -> ComposeResult:
        """Compose the setting item."""
        yield Label(self.label_text, classes="setting-label")
        yield Label(self.description_text, classes="setting-description")
        # Replace dots with hyphens for valid widget ID
        switch_id = f"switch-{self.setting_key.replace('.', '-')}"
        yield Switch(value=self.initial_value, id=switch_id)


class InitSettingsView(Container):
    """Settings view for initialization options."""

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize view."""
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the settings view."""
        yield Label("Initialization Settings", classes="section-title")

        yield SettingItem(
            "init.create_claude_md",
            "Create CLAUDE.md",
            "Generate CLAUDE.md configuration file",
            self.config.get("init.create_claude_md", True),
        )

        yield SettingItem(
            "init.create_gitignore_entries",
            "Update .gitignore",
            "Add Claude Code entries to .gitignore",
            self.config.get("init.create_gitignore_entries", True),
        )

        yield SettingItem(
            "init.overwrite_existing",
            "Overwrite Existing Files",
            "Replace existing Claude Code files during init",
            self.config.get("init.overwrite_existing", False),
        )


class ClaudeFeaturesView(Container):
    """Settings view for .claude/ directory features."""

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize view."""
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the settings view."""
        yield Label("Claude Directory Features", classes="section-title")
        yield Label(
            "Enable features to create in .claude/ directory",
            classes="section-subtitle",
        )

        yield SettingItem(
            "claude.create_settings",
            "Team Settings (settings.json)",
            "Shared permissions, hooks, and environment variables",
            self.config.get("claude.create_settings", False),
        )

        yield SettingItem(
            "claude.create_settings_local",
            "Personal Settings (settings.local.json)",
            "Personal project-specific overrides (gitignored)",
            self.config.get("claude.create_settings_local", False),
        )

        yield SettingItem(
            "claude.create_commands",
            "Slash Commands (commands/)",
            "Custom slash command definitions",
            self.config.get("claude.create_commands", False),
        )

        yield SettingItem(
            "claude.create_agents",
            "Sub-Agents (agents/)",
            "Custom AI sub-agents for specialized tasks",
            self.config.get("claude.create_agents", False),
        )

        yield SettingItem(
            "claude.create_hooks",
            "Hooks (hooks/)",
            "Pre/post tool execution scripts for automation",
            self.config.get("claude.create_hooks", False),
        )

        yield SettingItem(
            "claude.create_output_styles",
            "Output Styles (output-styles/)",
            "Custom Claude Code behavior profiles",
            self.config.get("claude.create_output_styles", False),
        )

        yield SettingItem(
            "claude.create_statusline",
            "Status Line (statusline.sh)",
            "Custom status bar display script",
            self.config.get("claude.create_statusline", False),
        )

        yield SettingItem(
            "claude.create_mcp",
            "MCP Servers (mcp/)",
            "Model Context Protocol server configurations",
            self.config.get("claude.create_mcp", False),
        )


class SettingsPanel(Container):
    """Settings panel with category navigation and setting views."""

    active_category: reactive[str] = reactive("init")

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize settings panel."""
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the settings panel."""
        with Horizontal(id="settings-container"):
            # Left: Category navigation
            with Vertical(id="settings-categories"):
                yield Button("Initialization", id="cat-init", classes="category-button")
                yield Button(
                    "Claude Features", id="cat-claude", classes="category-button"
                )

            # Right: Settings view
            with Vertical(id="settings-content"):
                yield InitSettingsView(self.config, id="view-init")
                yield ClaudeFeaturesView(self.config, id="view-claude")
                yield SaveNotification(id="save-notification")

    def on_mount(self) -> None:
        """Handle mount event."""
        self._show_category("init")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle category button press."""
        button_id = event.button.id
        if button_id and button_id.startswith("cat-"):
            category = button_id.replace("cat-", "")
            self._show_category(category)
            event.stop()  # Prevent bubbling to parent

    def _show_category(self, category: str) -> None:
        """Show the specified category view."""
        self.active_category = category

        # Update category button styling
        for button in self.query(".category-button"):
            if button.id == f"cat-{category}":
                button.add_class("active")
            else:
                button.remove_class("active")

        # Show/hide views
        init_view = self.query_one("#view-init")
        claude_view = self.query_one("#view-claude")

        if category == "init":
            init_view.display = True
            claude_view.display = False
        elif category == "claude":
            init_view.display = False
            claude_view.display = True

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle - auto-save."""
        switch_id = event.switch.id
        if not switch_id or not switch_id.startswith("switch-"):
            return

        # Find the SettingItem parent to get the original setting_key
        setting_item = next(
            (ancestor for ancestor in event.switch.ancestors if isinstance(ancestor, SettingItem)),
            None
        )
        if not setting_item:
            return

        setting_key = setting_item.setting_key

        # Update config
        self.config.set(setting_key, event.value)

        # Save to disk
        config_path = Path.cwd() / ".claudefig.toml"
        self.config.save(config_path)

        # Show save notification
        self._show_save_notification()

    def _show_save_notification(self) -> None:
        """Briefly show save notification."""
        notification = self.query_one("#save-notification", SaveNotification)
        notification.display = True
        self.set_timer(1.5, lambda: setattr(notification, "display", False))


class InitializePanel(Container):
    """Initialize project info panel with config summary."""

    def __init__(self, config: Config, on_review_settings, **kwargs) -> None:
        """Initialize panel.

        Args:
            config: Config instance
            on_review_settings: Callback to switch to settings panel
        """
        super().__init__(**kwargs)
        self.config = config
        self.on_review_settings_callback = on_review_settings

    def compose(self) -> ComposeResult:
        """Compose the initialize panel."""
        yield Label("Before You Begin", classes="panel-title")
        yield Label(
            "Make sure your settings are configured correctly before initializing this repository.",
            classes="panel-info",
        )

        yield Label("Current Configuration Summary:", classes="config-summary-title")

        # Build config summary
        summary = []
        summary.append(
            f"  CLAUDE.md Creation:        {'✓ Enabled' if self.config.get('init.create_claude_md', True) else '✗ Disabled'}"
        )
        summary.append(
            f"  Gitignore Updates:         {'✓ Enabled' if self.config.get('init.create_gitignore_entries', True) else '✗ Disabled'}"
        )
        summary.append(
            f"  Overwrite Existing Files:  {'✓ Enabled' if self.config.get('init.overwrite_existing', False) else '✗ Disabled'}"
        )

        # Count enabled Claude features
        claude_features = [
            "create_settings",
            "create_settings_local",
            "create_commands",
            "create_agents",
            "create_hooks",
            "create_output_styles",
            "create_statusline",
            "create_mcp",
        ]
        enabled_count = sum(
            1
            for feature in claude_features
            if self.config.get(f"claude.{feature}", False)
        )
        summary.append(f"  Claude Features Enabled:   {enabled_count} of 8")

        yield Label("\n".join(summary), classes="config-summary")

        # Action buttons
        with Horizontal(classes="button-row"):
            yield Button("Review Settings", id="btn-review-settings", variant="primary")
            yield Button("Start Initialization", id="btn-start-init")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-review-settings":
            self.on_review_settings_callback()
            event.stop()  # Prevent bubbling to parent
        elif event.button.id == "btn-start-init":
            # TODO: Implement initialization flow
            self.app.notify("Initialization wizard coming soon!")
            event.stop()  # Prevent bubbling to parent


class ContentPanel(Container):
    """Dynamic content panel that displays based on selection."""

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize the content panel."""
        super().__init__(**kwargs)
        self.config = config
        self.current_section: str | None = None

    def show_section(self, section: str) -> None:
        """Display content for the specified section."""
        # Don't remount if we're already showing this section
        if self.current_section == section and self.children:
            return

        self.current_section = section

        # Remove all children widgets to avoid ID conflicts
        for child in list(self.children):
            child.remove()

        # Mount appropriate panel
        if section == "init":
            self.mount(
                InitializePanel(self.config, self._switch_to_settings, id="init-panel")
            )
        elif section == "settings":
            self.mount(SettingsPanel(self.config, id="settings-panel"))
        elif section == "components":
            # TODO: Implement components panel
            self.mount(
                Label(
                    "Manage Components\n\nCLAUDE.md composition and customization\n(Coming soon)",
                    classes="placeholder",
                )
            )

        self.display = True

    def _switch_to_settings(self) -> None:
        """Switch to settings section."""
        # This will be called from InitializePanel
        main_app = self.app
        if isinstance(main_app, MainScreen):
            main_app._activate_section("settings")

    def clear(self) -> None:
        """Clear the content panel."""
        self.current_section = None
        self.remove_children()
        self.display = False


class MainScreen(App):
    """Main claudefig TUI application with side-by-side layout."""

    TITLE = "claudefig"
    SUB_TITLE = f"v{__version__}"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #menu-panel {
        width: 40;
        height: 100%;
        padding: 1 2;
    }

    #title {
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
        margin-top: 1;
    }

    #version {
        color: $text-muted;
        margin-bottom: 2;
    }

    #menu-buttons {
        width: 100%;
        height: auto;
        border: round $primary;
        padding: 1;
    }

    Button {
        width: 100%;
        margin: 0;
        min-height: 1;
        padding: 0 1;
        background: $panel;
    }

    Button:focus {
        text-style: bold;
        border: solid $accent;
    }

    Button.active {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    Button.active:focus {
        background: $accent;
        color: $text;
        text-style: bold;
        border: solid $accent;
    }

    #content-panel {
        width: 1fr;
        height: 100%;
        border-left: solid $primary;
        padding: 2 4;
        display: none;
    }

    #content-panel.visible {
        display: block;
    }

    /* Settings Panel Styles */
    #settings-container {
        width: 100%;
        height: 100%;
    }

    #settings-categories {
        width: 30;
        height: auto;
        border: round $primary;
        padding: 1;
        margin: 4 1 0 2;
    }

    .category-button {
        width: 100%;
        margin-bottom: 0;
        text-align: left;
    }

    .category-button.active {
        background: $accent-darken-1;
        color: $text;
    }

    #settings-content {
        width: 1fr;
        height: 100%;
        padding: 0 2;
        overflow-y: auto;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
        margin-top: 1;
    }

    .section-subtitle {
        color: $text-muted;
        margin-bottom: 2;
    }

    SettingItem {
        width: 100%;
        height: auto;
        margin-bottom: 2;
        layout: vertical;
    }

    .setting-label {
        text-style: bold;
        color: $text;
    }

    .setting-description {
        color: $text-muted;
        margin-bottom: 1;
    }

    #save-notification {
        dock: bottom;
        align: right top;
        padding: 1 2;
        background: $success;
        color: $text;
        border: solid $success-darken-1;
        display: none;
        width: auto;
        height: auto;
        margin-right: 2;
    }

    /* Initialize Panel Styles */
    .panel-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        margin-top: 1;
    }

    .panel-info {
        color: $text-muted;
        margin-bottom: 2;
    }

    .config-summary-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .config-summary {
        color: $text-muted;
        margin-bottom: 2;
        padding: 1;
        background: $panel;
        border: solid $primary-lighten-1;
    }

    .button-row {
        width: 100%;
        height: auto;
        margin-top: 2;
    }

    .button-row Button {
        width: auto;
        margin-right: 2;
    }

    .placeholder {
        color: $text-muted;
        text-align: center;
        margin-top: 4;
    }

    #view-claude {
        display: none;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        Binding("escape", "clear_selection", "Back", key_display="esc"),
        Binding("backspace", "clear_selection", "Back", show=False),
        Binding("left", "navigate_left", "Nav Left", show=True),
        Binding("right", "navigate_right", "Nav Right", show=True),
        Binding("up", "navigate_up", "Nav Up", show=True),
        Binding("down", "navigate_down", "Nav Down", show=True),
    ]

    active_button: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs):
        """Initialize the app."""
        super().__init__(**kwargs)
        self.config = Config()

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Horizontal(id="main-container"):
            # Left panel - Menu
            with Vertical(id="menu-panel"):
                yield Static("claudefig", id="title")
                yield Static(f"v{__version__}", id="version")

                with Container(id="menu-buttons"):
                    yield Button("Initialize Project", id="init")
                    yield Button("Settings", id="settings")
                    yield Button("Components", id="components")
                    yield Button("Exit", id="exit")

            # Right panel - Content
            yield ContentPanel(self.config, id="content-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Set focus to first button on mount."""
        from claudefig.user_config import ensure_user_config

        # Initialize user config on first launch
        ensure_user_config(verbose=True)

        self.query_one("#init", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if not button_id:
            return

        # Don't handle button presses from child panels
        if button_id.startswith(("cat-", "btn-", "switch-")):
            return

        if button_id == "exit":
            self.exit()
            return

        # Activate the section
        self._activate_section(button_id)

    def _activate_section(self, section_id: str) -> None:
        """Activate a section and update UI accordingly."""
        # Update active button state
        self.active_button = section_id

        # Update button styling
        for button in self.query("#menu-buttons Button"):
            if button.id == section_id:
                button.add_class("active")
            else:
                button.remove_class("active")

        # Show content panel
        content_panel = self.query_one("#content-panel", ContentPanel)
        content_panel.show_section(section_id)
        content_panel.add_class("visible")

        # Auto-focus first item in the new content tree
        self.set_timer(0.05, self._focus_first_in_content)

    def _focus_first_in_content(self) -> None:
        """Focus the first focusable widget in the content panel."""
        try:
            content_panel = self.query_one("#content-panel", ContentPanel)
            focusables = [w for w in content_panel.query("Button, Switch") if w.focusable]
            if focusables:
                focusables[0].focus()
        except Exception:
            pass

    def action_clear_selection(self) -> None:
        """Clear the active selection and hide content panel."""
        # Remember which button was active
        previously_active = self.active_button

        # Clear active button styling
        for button in self.query("#menu-buttons Button"):
            button.remove_class("active")

        # Hide content panel
        content_panel = self.query_one("#content-panel", ContentPanel)
        content_panel.clear()
        content_panel.remove_class("visible")

        self.active_button = None

        # Refocus the previously active button, or default to init
        if previously_active:
            try:
                self.query_one(f"#{previously_active}", Button).focus()
            except Exception:
                self.query_one("#init", Button).focus()
        else:
            self.query_one("#init", Button).focus()

    def _is_descendant_of(self, widget, ancestor) -> bool:
        """Check if widget is a descendant of ancestor."""
        current = widget.parent
        while current is not None:
            if current == ancestor:
                return True
            current = current.parent
        return False

    def action_navigate_right(self) -> None:
        """Navigate right: menu → content (if section open), or categories → settings."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in the menu panel
        menu_panel = self.query_one("#menu-panel")
        if self._is_descendant_of(focused, menu_panel):
            # Only move to content panel if a section is already active
            if self.active_button:
                content_panel = self.query_one("#content-panel", ContentPanel)
                # Try to focus the first focusable widget in content
                focusables = [w for w in content_panel.query("Button, Switch") if w.focusable]
                if focusables:
                    focusables[0].focus()
            # Don't activate section with right arrow - require Enter
            return

        # Check if we're in settings categories
        try:
            settings_categories = self.query_one("#settings-categories")
            if self._is_descendant_of(focused, settings_categories):
                # Move to settings content
                settings_content = self.query_one("#settings-content")
                focusables = [w for w in settings_content.query("Switch") if w.focusable]
                if focusables:
                    focusables[0].focus()
        except Exception:
            pass

    def action_navigate_left(self) -> None:
        """Navigate left: content → menu, or settings → categories."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in settings content
        try:
            settings_content = self.query_one("#settings-content")
            if self._is_descendant_of(focused, settings_content):
                # Move to settings categories
                settings_categories = self.query_one("#settings-categories")
                focusables = [w for w in settings_categories.query("Button") if w.focusable]
                if focusables:
                    focusables[0].focus()
                return
        except Exception:
            pass

        # Check if we're in content panel
        content_panel = self.query_one("#content-panel")
        if self._is_descendant_of(focused, content_panel):
            # Move back to the active menu button
            if self.active_button:
                menu_button = self.query_one(f"#{self.active_button}", Button)
                menu_button.focus()

    def _get_focus_scope(self, widget):
        """Get the container that defines the focus scope for a widget."""
        # Define scope containers (independent vertical navigation trees)
        scope_ids = ["menu-buttons", "settings-categories", "settings-content", "init-panel"]

        for scope_id in scope_ids:
            try:
                scope = self.query_one(f"#{scope_id}")
                if self._is_descendant_of(widget, scope) or widget == scope:
                    return scope
            except Exception:
                continue

        # Fallback to content panel for other content
        try:
            content_panel = self.query_one("#content-panel")
            if self._is_descendant_of(widget, content_panel):
                return content_panel
        except Exception:
            pass

        return None

    def action_navigate_up(self) -> None:
        """Navigate up within the current focus scope."""
        focused = self.focused
        if not focused:
            return

        scope = self._get_focus_scope(focused)
        if not scope:
            self.screen.focus_previous()
            return

        # Get all focusable widgets in this scope
        focusables = [w for w in scope.query("Button, Switch") if w.focusable]
        if not focusables:
            return

        try:
            current_index = focusables.index(focused)
            if current_index > 0:
                focusables[current_index - 1].focus()
        except ValueError:
            # Not in the list, focus first
            if focusables:
                focusables[0].focus()

    def action_navigate_down(self) -> None:
        """Navigate down within the current focus scope."""
        focused = self.focused
        if not focused:
            return

        scope = self._get_focus_scope(focused)
        if not scope:
            self.screen.focus_next()
            return

        # Get all focusable widgets in this scope
        focusables = [w for w in scope.query("Button, Switch") if w.focusable]
        if not focusables:
            return

        try:
            current_index = focusables.index(focused)
            if current_index < len(focusables) - 1:
                focusables[current_index + 1].focus()
        except ValueError:
            # Not in the list, focus first
            if focusables:
                focusables[0].focus()


class ClaudefigApp(MainScreen):
    """Alias for backward compatibility."""

    pass


if __name__ == "__main__":
    app = MainScreen()
    app.run()
