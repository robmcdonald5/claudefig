# Testing Plan: Hover Flash Issue

## Current Status
We've tried multiple fixes without empirical confirmation of the root cause. This document outlines systematic testing approaches.

---

## Test 1: Diagnostic Logging (RECOMMENDED FIRST)

**Purpose**: Capture exact sequence of Enter/Leave/Focus/Blur events

**Steps**:
1. Run diagnostic version:
   ```bash
   python -m claudefig.tui.app_diagnostics
   ```

2. Navigate to a section (e.g., press Enter on "Presets")

3. Press Escape or Backspace to go back

4. Check stderr output for event sequence - look for:
   - Which button received ENTER event
   - When it happened relative to FOCUS events
   - Timing of "LEAVE" events

**What to Look For**:
- Does Exit button receive an ENTER event during clear_selection?
- Does the ENTER happen before or after the FOCUS event?
- Are there unexpected LEAVE events?

**Share the output** so we can analyze the exact event sequence.

---

## Test 2: CSS Hover Suppression (CURRENTLY ACTIVE)

**Purpose**: Verify if the flash is hover-related

**Current State**:
- `styles.tcss` lines 55-57 disable hover visual feedback on menu buttons
- This is a diagnostic test, not a permanent solution

**Steps**:
1. Run normal TUI:
   ```bash
   claudefig interactive
   ```

2. Navigate to a section and press Escape

3. Observe if the flash still occurs

**Expected Results**:
- **If flash is gone**: Confirms it's a hover state issue
- **If flash persists**: It's something else (focus ring? border? different element?)

---

## Test 3: Identify the Flashing Element

**Purpose**: Confirm which exact element is showing the flash

**Steps**:
1. When you see the flash, note:
   - Is it definitely the "Exit" button?
   - Is it showing hover styling (lighter background)?
   - Or is it showing focus styling (bold text, border)?
   - Could it be a different element entirely?

2. Try moving your mouse to different positions before pressing Escape:
   - Mouse over Exit button → press Escape
   - Mouse over content panel → press Escape
   - Mouse completely off the TUI window → press Escape

3. Does the flash position change based on mouse position?

---

## Test 4: Alternative Layout Approach

**Purpose**: Test if removing layout changes prevents the flash

**Modify `app.py` action_clear_selection**:
```python
def action_clear_selection(self) -> None:
    """Clear the active selection and hide content panel."""
    previously_active = self.active_button

    # DON'T hide the content panel - just clear focus
    for button in self.query("#menu-buttons Button"):
        button.remove_class("active")

    self.active_button = None

    if previously_active:
        try:
            self.query_one(f"#{previously_active}", Button).focus()
        except Exception:
            self.query_one("#init", Button).focus()
    else:
        self.query_one("#init", Button).focus()

    # SKIP hiding content panel for this test
    # content_panel = self.query_one("#content-panel", ContentPanel)
    # content_panel.clear()
    # content_panel.remove_class("visible")
```

**Expected Result**:
- If flash is gone: Confirms the issue is related to hiding the content panel
- If flash persists: Something else is causing it

---

## Test 5: Timing Test

**Purpose**: Determine if adding more delay helps

**Modify `app.py`**:
```python
def action_clear_selection(self) -> None:
    """Clear the active selection and hide content panel."""
    previously_active = self.active_button

    for button in self.query("#menu-buttons Button"):
        button.remove_class("active")

    self.active_button = None

    # Focus immediately
    if previously_active:
        try:
            self.query_one(f"#{previously_active}", Button).focus()
        except Exception:
            self.query_one("#init", Button).focus()
    else:
        self.query_one("#init", Button).focus()

    # DELAY hiding content panel
    self.set_timer(0.1, self._delayed_hide_content)

def _delayed_hide_content(self) -> None:
    """Hide content panel after delay."""
    content_panel = self.query_one("#content-panel", ContentPanel)
    content_panel.clear()
    content_panel.remove_class("visible")
```

**Expected Result**:
- If flash is gone: It's a timing/race condition
- If flash persists: Delay doesn't help

---

## Summary of Current Code State

**app.py**:
- action_clear_selection focuses button BEFORE hiding content panel
- No timer delay (synchronous operations)

**styles.tcss**:
- content-panel uses `display: none` when hidden
- Menu button hover is DISABLED (Test #2 active)

**Diagnostic tool**:
- `app_diagnostics.py` logs all Enter/Leave/Focus/Blur events

---

## Next Steps

1. **Run Test #1** (diagnostic logging) and share the output
2. **Run Test #2** (check if flash occurs with hover disabled)
3. Based on results, we'll know whether to:
   - Fix hover state management
   - Fix focus timing
   - Look for a different element causing the flash
   - Investigate Textual framework behavior

The key is **getting empirical data** rather than making more guesses.
