from argparse import ArgumentParser
from junefeed.config import Config
from junefeed.app import Junefeed


def parse_args():
    parser = ArgumentParser(description='Junefeed - A simple RSS feed reader')
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='Junefeed v0.1.0',
        help='Show the version of Junefeed',
    )
    subparser = parser.add_subparsers(
        title='commands', dest='command', required=False, help='Available commands'
    )
    parser_add = subparser.add_parser('add', help='Add a new feed')
    parser_add.add_argument(
        '-n',
        '--name',
        type=str,
        required=True,
        help='a unique abbreviated name for the feed',
    )
    parser_add.add_argument(
        '-u',
        '--url',
        type=str,
        required=True,
        help='the feed URL, e.g. https://www.myfeed.com/myfeed.rss',
    )
    parser_remove = subparser.add_parser('remove', help='Remove a feed')
    parser_remove.add_argument(
        '-n', '--name', type=str, required=True, help='the unique name of the feed'
    )
    return parser.parse_args()


def main():
    """Entrypoint to the Junefeed app."""
    args = parse_args()
    config = Config()
    if args.command == 'add':
        config.add_feed(args.name, args.url)
    elif args.command == 'remove':
        config.remove_feed(args.name)
    if not args.command:
        app = Junefeed()
        app.run()


if __name__ == '__main__':
    main()
