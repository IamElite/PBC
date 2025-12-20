from pathlib import Path
import importlib

def list_modules():
    mod_dir = Path(__file__).parent
    return [
        file.stem
        for file in mod_dir.glob("*.py")
        if file.is_file() and file.name != "__init__.py"
    ]

ALL_MODULES = frozenset(sorted(list_modules()))

# Note: Modules are imported in __main__.py to avoid circular imports
