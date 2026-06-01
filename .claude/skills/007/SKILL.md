```markdown
# 007 Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the "007" Python repository. You'll learn how to structure files, organize imports and exports, write and locate tests, and follow commit and workflow conventions unique to this codebase. While no specific frameworks or automated workflows are detected, the repository demonstrates clear patterns for maintainable Python development.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `my_module.py`, `data_processor.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import helper_function
    from .models import DataModel
    ```

### Export Style
- Use **named exports** by explicitly listing exported symbols in `__all__`.
  - Example:
    ```python
    __all__ = ['MyClass', 'my_function']
    ```

### Commit Messages
- Use the `feat` prefix for new features.
- Commit messages are mixed in type but average around 83 characters.
  - Example: `feat: add data validation for user input`

## Workflows

### Adding a New Module
**Trigger:** When you need to add new functionality to the codebase  
**Command:** `/add-module`

1. Create a new Python file using snake_case (e.g., `new_feature.py`).
2. Implement your functions or classes.
3. Use relative imports to access existing modules.
4. Add your symbols to `__all__` for named exports.
5. Write corresponding test files following the testing pattern.
6. Commit with a message starting with `feat:`.

### Running Tests
**Trigger:** When you want to verify code correctness  
**Command:** `/run-tests`

1. Locate test files matching the `*.test.*` pattern (e.g., `utils.test.py`).
2. Use the preferred Python test runner (e.g., `pytest`, `unittest`).
   - Example:
     ```bash
     python -m unittest discover
     ```
3. Review test results and fix any failures.

## Testing Patterns

- Test files follow the `*.test.*` naming pattern (e.g., `module.test.py`).
- The specific testing framework is not enforced; use standard Python testing tools.
- Place tests alongside or near the modules they test.
- Example test file:
  ```python
  # utils.test.py
  import unittest
  from .utils import helper_function

  class TestHelperFunction(unittest.TestCase):
      def test_basic(self):
          self.assertEqual(helper_function(2), 4)
  ```

## Commands
| Command      | Purpose                                 |
|--------------|-----------------------------------------|
| /add-module  | Scaffold and add a new Python module    |
| /run-tests   | Run all tests in the repository         |
```
