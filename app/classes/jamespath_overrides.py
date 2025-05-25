from typing import Dict


class JamesPathDictMerger:
    @staticmethod
    def set_by_jamespath(dct, jamespath, value):
        keys = jamespath.split(".")
        for key in keys[:-1]:
            if key not in dct or not isinstance(dct[key], dict):
                dct[key] = {}
            dct = dct[key]
        dct[keys[-1]] = value

    @staticmethod
    def get_by_jamespath(dct, jamespath):
        keys = jamespath.split(".")
        for key in keys:
            if isinstance(dct, dict) and key in dct:
                dct = dct[key]
            else:
                return None
        return dct

    @staticmethod
    def has_jamespath(dct, jamespath):
        keys = jamespath.split(".")
        for key in keys[:-1]:
            if isinstance(dct, dict) and key in dct:
                dct = dct[key]
            else:
                return False
        return isinstance(dct, dict) and keys[-1] in dct

    @classmethod
    def selective_override(cls, base: Dict, override: Dict, jamespaths_defaults: Dict) -> Dict:
        """
        jamespaths_defaults: dict mapping jamespath string → default value
        For each path:
          - If override value is not None, use it.
          - If override value is None (and key exists in override), use default.
          - If override key is missing, use default.
        """
        for path, default_value in jamespaths_defaults.items():
            if cls.has_jamespath(override, path):
                value = cls.get_by_jamespath(override, path)
                if value is not None:
                    cls.set_by_jamespath(base, path, value)
                else:
                    cls.set_by_jamespath(base, path, default_value)
            else:
                cls.set_by_jamespath(base, path, default_value)
        return base


# Example usage:
if __name__ == "__main__":
    base = {"name": "Nautical Backup config", "description": "desc"}

    override = {
        "match": {
            "container_id": "123abc",
            "container_label": "container_1",
            "container_image": "minituff/nautical-backup",
        }
    }

    jamespaths_defaults = {
        "name": "Default Name",
        "match.container_name": "Default Container",
        "match.container_id": None,
        "match.container_label": "N/A",
        "match.container_image": None,
        "description": "Default Description",
    }

    JamesPathDictMerger.selective_override(base, override, jamespaths_defaults)

    print(base)
