import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_script_module(module_name: str, script_path: Path) -> ModuleType:
    """Load one script as a module while making sibling imports resolvable."""
    script_directory = str(script_path.parent)
    sys.path.insert(0, script_directory)
    try:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load {module_name} from {script_path}")
        module = importlib.util.module_from_spec(spec)
        had_previous_module = module_name in sys.modules
        previous_module = sys.modules.get(module_name)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            if had_previous_module:
                sys.modules[module_name] = previous_module
            else:
                sys.modules.pop(module_name, None)
            raise
    finally:
        sys.path.remove(script_directory)
    return module
