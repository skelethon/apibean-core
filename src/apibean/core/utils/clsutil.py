import importlib
import inspect
import pkgutil

def find_classes_with_metaclass(package, meta):
    found_classes = []

    # Loop through all modules in the package
    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            continue

        # Inspect all classes defined in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Make sure the class is defined in the current module
            if obj.__module__ != module.__name__:
                continue
            # Check if it uses the target metaclass
            if type(obj) is meta:
                found_classes.append(obj)

    return found_classes
