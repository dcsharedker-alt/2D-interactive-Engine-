import os
import importlib.util
import sys

def load_module(module_name: str):
    target_path = os.path.join("modules", module_name, "main.py")
    
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Module {module_name} is not installed at {target_path}.")

    module_dir = os.path.join("modules", module_name)
    if module_dir not in sys.path:
        sys.path.append(module_dir)

    spec = importlib.util.spec_from_file_location(f"dynamic_{module_name}", target_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load specification for module {module_name}.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module