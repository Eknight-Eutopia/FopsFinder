from pathlib import Path
from typing import Any

import yaml


def load_config(config_dir: str | Path | None = None) -> dict[str, Any]:
    """Load config.yaml as the sole application configuration file."""
    directory = Path(__file__).resolve().parent if config_dir is None else Path(config_dir)
    yaml_path = directory / "config.yaml"
    with yaml_path.open("r", encoding="utf-8") as source:
        values = yaml.safe_load(source)
    if not isinstance(values, dict):
        raise TypeError(f"{yaml_path} must contain a configuration mapping")
    return values


config = load_config()

if __name__ == "__main__":
    config = load_config()
    print(config)
