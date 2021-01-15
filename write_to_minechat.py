import argparse
from dotenv import dotenv_values

import asyncio
import json

from connection import open_asyncio_connection
from config import HOST, WRITE_PORT

import logging

logger = logging.getLogger(__name__)


class InvalidToken(Exception):
    pass


async def write_to_chat(host, port, account_hash, message):
    async with open_asyncio_connection(host, port) as rw_descriptor:
        reader, writer = rw_descriptor

        data = await reader.readline()
        logger.debug(data.decode())

        await authorise(reader, writer, account_hash)

        data = await reader.readline()
        logger.debug(data.decode())

        await submit_message(writer, message)


async def authorise(reader, writer, account_hash):
    writer.writelines([account_hash.encode(), b'\n'])
    await writer.drain()

    data = await reader.readline()
    logger.debug(data.decode())

    account_dict = json.loads(data) if data.decode().strip() else None

    if not account_dict:
        error_message = 'Неизвестный токен. Проверьте его или зарегистрируйте заново.'
        logger.debug(error_message)

        assert False, error_message

    return account_dict


async def submit_message(writer, message):
    message = sanitize(message)

    writer.writelines([message.encode(), b'\n' * 2])
    await writer.drain()


async def register(host, port, nickname) -> dict:
    async with open_asyncio_connection(host, port) as rw_descriptor:
        reader, writer = rw_descriptor

        data = await reader.readline()
        logger.debug(data.decode())

        writer.write(b'\n')
        await writer.drain()

        data = await reader.readline()
        logger.debug(data.decode())

        nickname = sanitize(nickname)
        writer.writelines([nickname.encode(), b'\n'])
        await writer.drain()

        data = await reader.readline()
        logger.debug(data.decode())

        return json.loads(data)


def sanitize(text: str) -> str:
    return text.replace('\n', '')


def parse_args(host, port, token):
    parser = argparse.ArgumentParser(description='Отправляем сообщение в чат.')

    parser.add_argument('--host', default=host)
    parser.add_argument('--port', default=port)

    parser.add_argument('-n', '--nickname', '-u', '--username')
    parser.add_argument('-r', '--registration', action='store_true',
                        help='Регистрация пользователя. Используется вместе c параметром NICKNAME')

    parser.add_argument('-t', '--token', default=token)
    parser.add_argument('-m', '--message',
                        help='Отправить сообщение. Используется вместе c параметром TOKEN')

    return parser.parse_args()


def main():
    values_dict = dotenv_values()

    host = values_dict.get('HOST', HOST)
    port = values_dict.get('WRITE_PORT', WRITE_PORT)
    token = values_dict.get('TOKEN')

    args = parse_args(host, port, token)

    if args.registration:
        account_dict = asyncio.run(
            register(args.host, args.port, args.nickname)
        )
        print(
            'NICKNAME: {}\n'
            'TOKEN: {}'.format(account_dict['nickname'], account_dict['account_hash'])
        )

    elif not args.token:
        print('Укажите токен.')


    elif args.message:
        asyncio.run(
            write_to_chat(args.host, args.port, args.token, args.message)
        )


if __name__ == '__main__':
    main()
