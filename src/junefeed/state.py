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
        assert hasattr(self, '_config')
        with open(self.config_file, 'w') as file:
            yaml.dump(self._config, file)


class History:
    def __init__(self):
        history_dir = Path.home() / '.local' / 'state' / 'junefeed'
        history_dir.mkdir(exist_ok=True, parents=True)
        self.history_file = history_dir / 'history.json'
        if not self.history_file.exists():
            self._history = []
            self.write_history()
        else:
            with open(self.history_file, 'r') as file:
                self._history = json.load(file)

    def write_history(self):
        assert hasattr(self, '_history')
        with open(self.history_file, 'w') as file:
            json.dump(self._history, file, indent=2)


class Keybindings:
    def __init__(self):
        config_dir = Path.home() / '.config' / 'junefeed'
        config_dir.mkdir(exist_ok=True, parents=True)
        self.keybindings_file = config_dir / 'keybindings.yaml'

        if not self.keybindings_file.exists():
            self._set_defaults()
            self.write_keybindings()
        else:
            with open(self.keybindings_file, 'r') as file:
                self._keybindings = yaml.safe_load(file)
        assert isinstance(self._keybindings, dict), self._keybindings
        self._screens = list(self._keybindings.keys())
        self._actions = [act for screen in self._keybindings.values() for act in screen]

    def _set_defaults(self):
        self._keybindings = {
            'entry_collection_screen': {
                'scroll_down': ['j', 'down'],
                'scroll_up': ['k', 'up'],
                'open': ['o'],
                'mark_read_unread': ['m'],
                'hide_read': ['t'],
                'refresh': ['r'],
                'quit': ['q'],
            },
            'single_entry_screen': {
                'open': ['o'],
                'mark_read_unread': ['m'],
                'previous_screen': ['q'],
            },
            'feed_screen': {'previous_screen': ['q']},
        }

    def get_key(self, screen: str, action: str) -> list[str]:
        if screen not in self._screens:
            raise KeyError(f'Screen "{screen}" is not a valid screen name.')
        elif action not in self._actions:
            raise KeyError(f'"{action}" is not a valid action.')
        return self._keybindings[screen][action]

    def write_keybindings(self):
        assert hasattr(self, '_keybindings')
        with open(self.keybindings_file, 'w') as file:
            yaml.dump(self._keybindings, file)
