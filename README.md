# JuneFeed - An RSS reader for the terminal

[![Testing](https://github.com/jonathan-wells/junefeed/actions/workflows/test.yml/badge.svg)](https://github.com/jonathan-wells/junefeed/actions/workflows/test.yml)
[![Lint and format](https://github.com/jonathan-wells/junefeed/actions/workflows/lint_and_format.yml/badge.svg)](https://github.com/jonathan-wells/junefeed/actions/workflows/lint_and_format.yml)

JuneFeed is a simple RSS-feed reader for your terminal, allowing you to easily keep up with the
topics important to you. It is inspired by similar terminal-based RSS readers such as
[nom](https://github.com/guyfedwards/nom) and [newsboat](https://github.com/newsboat/newsboat).

## Installation
```
git clone https://github.com/jonathan-wells/junefeed
uv tool install junefeed
```

## Usage
```
$ june -h
usage: june [-h] [-v] {add,remove,keys} ...

Junefeed - A simple RSS feed reader

optional arguments:
  -h, --help         show this help message and exit
  -v, --version      Show the version of Junefeed

commands:
  {add,remove,keys}  Available commands
    add              Add a new feed
    remove           Remove a feed
    keys             Show key bindings
```
