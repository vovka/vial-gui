# Code Style Rules

## Class and Module Organization

- **One class per file**: Each class should be in its own file
- **100 lines limit per class**: Keep classes focused and under 100 lines
- **10 lines limit per method**: Methods should be concise and single-purpose
- **Package structure**: Group related classes into packages with `__init__.py` exports

## File Structure

```
package_name/
├── __init__.py          # Package exports
├── class_one.py         # One class per file
├── class_two.py
└── ...
```

## Naming Conventions

- **Files**: lowercase with underscores (e.g., `label_placer.py`)
- **Classes**: PascalCase (e.g., `ComboLabelPlacer`)
- **Methods**: lowercase with underscores (e.g., `compute_placement`)
- **Private methods**: prefix with underscore (e.g., `_score_position`)

## Code Organization Principles

- **Separation of concerns**: Each class handles one responsibility
- **Extract complexity**: Move complex logic into dedicated classes
- **Keep widget code simple**: UI widgets should delegate to helper classes
- **Prefer composition**: Build complex behavior from simple, focused classes

## Refactoring Guidelines

When code becomes complex:
1. Identify distinct responsibilities
2. Extract each into its own class
3. Create a package if multiple related classes exist
4. Use a renderer/orchestrator pattern for coordination
5. Keep data classes separate from logic classes
