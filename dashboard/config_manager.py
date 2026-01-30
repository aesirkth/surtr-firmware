import json


class ConfigManager:
    def __init__(self, initial_path):
        self._path = initial_path
        self._config = self._load_config(initial_path)

    def _load_config(self, path):
        """Load ADC config from JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: ADC config file not found at {path}. Using default values.")
            default_config = {
                "ADC0": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)},
                "ADC1": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)}
            }
            default_config["ADC0"]["context_label"] = ""
            default_config["ADC1"]["context_label"] = ""
            return default_config
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse ADC config file: {e}. Using default values.")
            default_config = {
                "ADC0": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)},
                "ADC1": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)}
            }
            default_config["ADC0"]["context_label"] = ""
            default_config["ADC1"]["context_label"] = ""
            return default_config

    def get_config(self):
        """Get the current config"""
        return self._config

    def get_path(self):
        """Get the current config path"""
        return self._path

    def load_from_path(self, path):
        """Load config from a new path"""
        self._path = path
        self._config = self._load_config(path)
        print(f"Config loaded from: {path}")
