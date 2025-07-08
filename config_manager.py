import json

CONFIG_FILE = "config.json"

def config_manager(new_config=None):
    """
    Якщо new_config не переданий — завантажує конфіг і повертає його.
    Якщо переданий словник new_config — просто повертає його, не перезаписуючи файл.
    """
    if new_config is None:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    else:
        # Не перезаписуємо файл, а просто повертаємо новий конфіг
        return new_config

