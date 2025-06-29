import os
import yaml


class Config:
    config_file = os.environ['HOME'] + '/.local/state/junefeed/config.yaml'
    history_file = os.environ['HOME'] + '/.local/state/junefeed/history.json'

    def __init__(self):
        with open(self.config_file, 'r') as config_file:
            self._config = yaml.safe_load(config_file)
        self.feeds = {
            feed['name']: feed['url'] for feed in self._config.get('feeds', [])
        }

    def add_feed(self, name: str, url: str) -> None:
        if name in self.feeds:
            raise KeyError(f'Feed "{name}" already exists')
        self.feeds[name] = url
        self._config['feeds'].append({'name': name, 'url': url})
        self._write_config()

    def remove_feed(self, name: str):
        if name not in self.feeds:
            return
        self.feeds.pop(name)
        idx = 0
        while idx < len(self._config['feeds']):
            if self._config['feeds'][idx].get('name') == name:
                break
            idx += 1
        self._config['feeds'].pop(idx)
        self._write_config()

    def _write_config(self) -> None:
        with open(self.config_file, 'w') as file:
            yaml.dump(self._config, file)


config = Config()
