# CLAUDE.md

---

# GENERAL RULES

## Agentic Workflow Principles **IMPORTANT**

1. **Outline**
   When prompted break up the task at hand into a tiered `todo list`.

2. **Delegate**
   Look at your context window to see what sub-agents are available. Delegate research tasks for information gathering on the tasks from the `todo list` to appropriate sub-agent(s) using `@'relevant-agent-name'` call(s). Always prompt researchers in parallel if the `todo list` has multiple points of information that needs gathered.

3. **Analyze**
   When a sub-agent is done outputting, analyze what it did and decide if the output is good or if the agent needs re-tasked with new instructions.

4. **Summarize**
   When `todo list` is completed or at break points where part of the `todo list` are completed, do an overview concisely describing what was completed. Be susinct and straight forward unless extra detail was requested.

---

## Quality & Standards

All agents when completing tasks must follow these standards.

- **Formatting/Linting**
  Apply appropriate formatters/linters for the project language and enforce them in CI.

- **Compaction**
  Make sure to keep track of progress and TODO lists through compactions.

- **Documentation**
  Follow industry standard best practices for code documentation appropriate to the project's language.

---

## Project Description

<!-- Describe your project here -->
This is a new project initialized with claudefig.

---

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
