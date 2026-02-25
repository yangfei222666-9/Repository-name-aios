# Contributing to AIOS

Thank you for your interest in contributing to AIOS! 🎉

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Guidelines](#coding-guidelines)
5. [Testing](#testing)
6. [Pull Request Process](#pull-request-process)
7. [Community](#community)

---

## Code of Conduct

This project follows a simple code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- No harassment or discrimination

---

## How Can I Contribute?

### Reporting Bugs

Found a bug? Please open an issue with:
- **Clear title** - Describe the problem concisely
- **Steps to reproduce** - How can we trigger the bug?
- **Expected behavior** - What should happen?
- **Actual behavior** - What actually happens?
- **Environment** - OS, Python version, AIOS version
- **Logs** - Relevant error messages or stack traces

**Example:**

```
Title: Reactor fails to execute playbook on Windows

Steps to reproduce:
1. Install AIOS v0.5 on Windows 11
2. Create playbook with "kill_process" action
3. Trigger playbook via event

Expected: Process should be killed
Actual: Error "Access denied"

Environment:
- OS: Windows 11 Pro
- Python: 3.12.10
- AIOS: 0.5.0

Logs:
[ERROR] Reactor: Failed to execute action 'kill_process'
PermissionError: [WinError 5] Access is denied
```

---

### Suggesting Features

Have an idea? Open an issue with:
- **Use case** - What problem does this solve?
- **Proposed solution** - How should it work?
- **Alternatives** - What other approaches did you consider?
- **Impact** - Who benefits from this feature?

---

### Contributing Code

We welcome pull requests! Here's how:

1. **Fork the repository**
2. **Create a feature branch** - `git checkout -b feature/my-feature`
3. **Make your changes** - Follow coding guidelines
4. **Add tests** - Ensure your code is tested
5. **Run tests** - Make sure everything passes
6. **Commit** - Use clear commit messages
7. **Push** - `git push origin feature/my-feature`
8. **Open a PR** - Describe your changes

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/aios.git
cd aios

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/
```

---

## Coding Guidelines

### Python Style

- Follow **PEP 8** (use `black` for formatting)
- Use **type hints** where appropriate
- Write **docstrings** for public functions/classes
- Keep functions **small and focused** (< 50 lines)
- Prefer **explicit over implicit**

**Example:**

```python
def calculate_score(
    success_rate: float,
    correction_rate: float,
    uptime: float,
    learning_rate: float
) -> float:
    """
    Calculate evolution score based on system metrics.
    
    Args:
        success_rate: Task success rate (0.0 to 1.0)
        correction_rate: Auto-correction rate (0.0 to 1.0)
        uptime: System uptime (0.0 to 1.0)
        learning_rate: Knowledge accumulation rate (0.0 to 1.0)
    
    Returns:
        Evolution score (0.0 to 1.0)
    """
    return (
        success_rate * 0.4 +
        correction_rate * 0.3 +
        uptime * 0.2 +
        learning_rate * 0.1
    )
```

### Code Organization

- **One class per file** (unless tightly coupled)
- **Group related functions** in modules
- **Use meaningful names** (no `x`, `tmp`, `data`)
- **Avoid deep nesting** (max 3 levels)

### Comments

- **Why, not what** - Explain reasoning, not mechanics
- **Keep comments up-to-date** - Outdated comments are worse than none
- **Use TODO/FIXME** - Mark areas needing improvement

**Good:**

```python
# Use exponential backoff to avoid overwhelming the API
retry_delay = base_delay * (2 ** attempt)
```

**Bad:**

```python
# Multiply base_delay by 2 to the power of attempt
retry_delay = base_delay * (2 ** attempt)
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_reactor.py

# Run with coverage
pytest --cov=aios tests/

# Run only fast tests (skip slow integration tests)
pytest -m "not slow" tests/
```

### Writing Tests

- **Test behavior, not implementation**
- **Use descriptive test names** - `test_reactor_executes_playbook_on_matching_event`
- **Follow AAA pattern** - Arrange, Act, Assert
- **Mock external dependencies** - Don't hit real APIs in tests

**Example:**

```python
def test_reactor_executes_playbook_on_matching_event():
    # Arrange
    reactor = Reactor()
    playbook = {
        "id": "test_playbook",
        "trigger": {"event_type": "test.event"},
        "actions": [{"type": "log", "params": {}}]
    }
    reactor.load_playbook(playbook)
    event = {"type": "test.event", "data": {}}
    
    # Act
    result = reactor.execute("test_playbook", event)
    
    # Assert
    assert result["success"] is True
    assert result["actions_executed"] == 1
```

---

## Pull Request Process

### Before Submitting

1. **Update documentation** - If you changed behavior, update docs
2. **Add tests** - New features need tests
3. **Run tests locally** - Make sure everything passes
4. **Update CHANGELOG.md** - Add your changes under "Unreleased"
5. **Rebase on main** - Ensure your branch is up-to-date

### PR Description

Include:
- **What** - What does this PR do?
- **Why** - Why is this change needed?
- **How** - How does it work?
- **Testing** - How did you test this?
- **Screenshots** - If UI changes, include before/after

**Example:**

```markdown
## What
Add support for custom playbook actions

## Why
Users want to extend Reactor with custom logic without modifying core code

## How
- Added `ActionRegistry` for registering custom actions
- Updated Reactor to look up actions in registry
- Added documentation and examples

## Testing
- Added unit tests for ActionRegistry
- Added integration test for custom action execution
- Manually tested with example custom action

## Breaking Changes
None
```

### Review Process

1. **Automated checks** - CI must pass (tests, linting)
2. **Code review** - At least one maintainer approval
3. **Discussion** - Address feedback and questions
4. **Merge** - Maintainer will merge when ready

---

## Community

### Getting Help

- **GitHub Issues** - For bugs and feature requests
- **Discord** - For questions and discussions (https://discord.gg/aios)
- **Email** - support@aios.dev

### Recognition

Contributors are recognized in:
- **CHANGELOG.md** - Your changes are documented
- **README.md** - Top contributors listed
- **GitHub** - Contributor badge on your profile

---

## Project Structure

```
aios/
├── core/               # Core components (EventBus, Scheduler, Reactor)
├── agent_system/       # Agent management and orchestration
├── memory/             # Memory Palace (knowledge storage)
├── learning/           # Learning and evolution engine
├── dashboard/          # Web dashboard
├── tests/              # Test suite
├── docs/               # Documentation
├── scripts/            # Utility scripts
└── examples/           # Example projects
```

---

## Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit files ...

# 3. Run tests
pytest tests/

# 4. Format code
black aios/

# 5. Commit
git add .
git commit -m "Add feature: my feature description"

# 6. Push
git push origin feature/my-feature

# 7. Open PR on GitHub
```

### Bug Fix

```bash
# 1. Create bugfix branch
git checkout -b fix/issue-123

# 2. Fix the bug
# ... edit files ...

# 3. Add regression test
# ... add test that would have caught the bug ...

# 4. Run tests
pytest tests/

# 5. Commit
git commit -m "Fix #123: description of fix"

# 6. Push and open PR
git push origin fix/issue-123
```

---

## Release Process

(For maintainers)

1. **Update version** - Bump version in `setup.py`
2. **Update CHANGELOG.md** - Move "Unreleased" to new version
3. **Create release branch** - `git checkout -b release/v0.6.0`
4. **Run full test suite** - `pytest tests/`
5. **Build package** - `python setup.py sdist bdist_wheel`
6. **Test installation** - Install in clean environment
7. **Tag release** - `git tag v0.6.0`
8. **Push to PyPI** - `twine upload dist/*`
9. **Create GitHub release** - Add release notes
10. **Announce** - Discord, Twitter, etc.

---

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion on GitHub
- Ask in Discord
- Email the maintainers

We're here to help! 🚀

---

**Thank you for contributing to AIOS!**

---

**Last Updated:** 2026-02-24  
**Maintainer:** 珊瑚海 (yangfei222666-9)  
**License:** MIT
