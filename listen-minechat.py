import argparse
from dotenv import dotenv_values

import asyncio

from heandler import handle_text
from utils import write_file
from connection import open_asyncio_connection

from config import HOST, READ_PORT, HISTORY_FILE


async def read_chat(host, port, filename):
    async with open_asyncio_connection(host, port, filename) as rw_descriptor:
        reader, writer = rw_descriptor

        while True:
            data = await reader.readline()

            message = data.decode()
            print(message.strip())

            await write_file(filename, handle_text(message))


def parse_args(host, port, history):
    parser = argparse.ArgumentParser(description='Слушаем чат.')

    parser.add_argument('--host', default=host)
    parser.add_argument('--port', default=port)
    parser.add_argument('--history', default=history, help='history file')

    return parser.parse_args()


def main():
    values_dict = dotenv_values()

    host = values_dict.get('HOST', HOST)
    port = values_dict.get('READ_PORT', READ_PORT)
    history = values_dict.get('HISTORY_FILE', HISTORY_FILE)

    args = parse_args(host, port, history)

    asyncio.run(
        read_chat(args.host, args.port, args.history)
    )


if __name__ == '__main__':
    main()
