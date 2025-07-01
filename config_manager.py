import json

CONFIG_FILE = "config.json"

def config_manager(new_config=None):
    """
    Якщо new_config не переданий — завантажує конфіг і повертає його.
    Якщо переданий словник new_config — перезаписує файл конфігу і повертає оновлений конфіг.
    """
    if new_config is None:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    else:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, ensure_ascii=False, indent=4)
        return new_config


# Для зручності можна одразу завантажувати конфіг глобально
CONFIG = config_manager()
