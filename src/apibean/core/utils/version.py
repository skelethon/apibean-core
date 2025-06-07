import os
from typing import Optional, Callable

try:
    import tomllib  # Python >= 3.11
except ImportError:
    import tomli as tomllib  # Python < 3.11

# Global cache
_version_cache = None

def get_app_version(pyproject_path: str = None, version_file_path: str = None,
        debuglog: Optional[Callable] = None) -> str:
    """
    Multi-source version detection (cached):
    - Priority 1: ENV variable APP_VERSION
    - Priority 2: VERSION file
    - Priority 3: pyproject.toml [project.version]

    Raises:
        RuntimeError if no version source is found.
    """
    global _version_cache
    if _version_cache is not None:
        return _version_cache

    # Use provided logger or fallback to default
    if not callable(debuglog):
        debuglog = lambda _: None

    # Priority 1: ENV
    env_version = os.getenv("APP_VERSION")
    if env_version:
        env_version = env_version.strip()
        _version_cache = env_version
        debuglog(f"[get_app_version] Using version from ENV APP_VERSION: {_version_cache}")
        return _version_cache

    # Priority 2: VERSION file
    if version_file_path:
        version_file_path = os.path.abspath(version_file_path)
        if os.path.exists(version_file_path):
            with open(version_file_path, "r", encoding="utf-8") as vf:
                file_version = vf.read().strip()
                if file_version:
                    _version_cache = file_version
                    debuglog(f"[get_app_version] Using version from VERSION file: {_version_cache}")
                    return _version_cache

    # Priority 3: pyproject.toml
    if pyproject_path:
        pyproject_path = os.path.abspath(pyproject_path)
        if os.path.exists(pyproject_path):
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
            try:
                _version_cache = pyproject.get("project", {}).get("version")
                debuglog(f"[get_app_version] Using version from pyproject.toml: {_version_cache}")
                return _version_cache
            except KeyError:
                raise RuntimeError(f"Could not find 'project.version' in {pyproject_path}")

    # If all sources fail
    raise RuntimeError("Could not determine version from ENV APP_VERSION, VERSION file, or pyproject.toml")
