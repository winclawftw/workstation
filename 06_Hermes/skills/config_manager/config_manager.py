class ConfigManager:
    def __init__(self):
        self.config = {}

    def load_config(self, config_data):
        self.config.update(config_data)

    def save_config(self):
        return self.config

    def get_config(self, key):
        return self.config.get(key, None)
