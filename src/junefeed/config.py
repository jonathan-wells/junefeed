from pathlib import Path
import json
import yaml


class Config:
    def __init__(self):
        config_dir = Path.home() / '.config' / 'junefeed'
        config_dir.mkdir(exist_ok=True, parents=True)
        self.config_file = config_dir / 'config.yaml'

        if not self.config_file.exists():
            self._config = {'feeds': []}
            with open(self.config_file, 'w') as file:
                yaml.dump(self._config, file)
        else:
            with open(self.config_file, 'r') as file:
                self._config = yaml.safe_load(file)
        assert isinstance(self._config, dict), self._config

        self.feeds = {
            feed['name']: feed['url'] for feed in self._config.get('feeds', [])
        }

    def add_feed(self, name: str, url: str) -> None:
        if name in self.feeds:
            raise KeyError(f'Feed "{name}" already exists')
        self.feeds[name] = url
        self._config['feeds'].append({'name': name, 'url': url})
        self.write_config()

    def remove_feed(self, name: str):
        if name not in self.feeds:
            raise KeyError(f'"{name}" was found in feed list')

        self.feeds.pop(name)
        idx = 0
        while idx < len(self._config['feeds']):
            if self._config['feeds'][idx].get('name') == name:
                break
            idx += 1
        self._config['feeds'].pop(idx)
        self.write_config()

    def write_config(self):
        with open(self.config_file, 'w') as file:
            yaml.dump(self._config, file)


class History:
    def __init__(self):
        history_dir = Path.home() / '.local' / 'state' / 'junefeed'
        history_dir.mkdir(exist_ok=True, parents=True)
        self.history_file = history_dir / 'history.json'
        if not self.history_file.exists():
            self._history = []
            with open(self.history_file, 'w') as file:
                json.dump(self._history, file)
        else:
            with open(self.history_file, 'r') as file:
                self._history = json.load(file)

    def write_history(self):
        with open(self.history_file, 'w') as file:
            json.dump(self._history, file, indent=2)
