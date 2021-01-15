import asyncio
import json
import logging
import os
from datetime import datetime
from tkinter import messagebox

import async_timeout
from dotenv import load_dotenv

import gui
from config import HISTORY_FILE, HOST, READ_PORT, WRITE_PORT
from connection import open_asyncio_connection
from heandler import handle_text
from utils import read_file, write_file
from write_to_minechat import write_to_chat

watchdog_logger = logging.getLogger()


class InvalidToken(Exception):
    pass


async def main(account_hash):
    queues_names = 'messages', 'sending', 'status_updates', 'saving', 'watchdog'
    queues = {queue_name: asyncio.Queue() for queue_name in queues_names}

    queues['watchdog'].put_nowait('Connection is alive. Source: Prompt before auth')

    async with open_asyncio_connection(HOST, WRITE_PORT) as rw_descriptor:

        reader, writer = rw_descriptor

        await reader.readline()

        try:
            account_dict = await authorise(reader, writer, account_hash)
        except InvalidToken:
            messagebox.showinfo("Ошибка авторизации", "Проверьте токен, сервер его не узнал.")

    queues['watchdog'].put_nowait('Connection is alive. Source: Authorization done')

    queues['messages'].put_nowait('Выполнена авторизация. Пользователь {}.\n'.format(account_dict['nickname']))

    loaded_messages = read_file(HISTORY_FILE)
    queues['messages'].put_nowait(loaded_messages)

    nickname = gui.NicknameReceived(account_dict['nickname'])
    queues['status_updates'].put_nowait(nickname)

    await asyncio.gather(
        gui.draw(queues['messages'], queues['sending'], queues['status_updates']),
        read_msgs(HOST, READ_PORT, queues),
        save_messages(HISTORY_FILE, queues['saving']),
        send_msgs(HOST, WRITE_PORT, queues, account_hash),
        watch_for_connection(queues['watchdog']),
    )


async def watch_for_connection(queue):
    timeout_seconds = 10
    while True:

        try:
            with async_timeout.timeout(timeout_seconds) as cm:
                message = await queue.get()
                watchdog_logger.info('[{}] {}'.format(datetime.now().timestamp(), message))

        except asyncio.TimeoutError:
            if cm.expired:
                watchdog_logger.info('{}s timeout is elapsed'.format(timeout_seconds))
                queue.put_nowait('{}s timeout is elapsed'.format(timeout_seconds))


async def authorise(reader, writer, account_hash):
    writer.writelines([account_hash.encode(), b'\n'])

    await writer.drain()

    data = await reader.readline()
    account_dict = json.loads(data) if data.decode().strip() else None

    if not account_dict:
        raise InvalidToken

    return account_dict


async def send_msgs(host, port, queues, account_hash):
    state = gui.SendingConnectionStateChanged

    queues['status_updates'].put_nowait(state.INITIATED)

    while True:
        message = await queues['sending'].get()
        queues['status_updates'].put_nowait(state.ESTABLISHED)
        queues['watchdog'].put_nowait('Connection is alive. Source: Message sent')

        await write_to_chat(host, port, account_hash, message)


async def save_messages(filepath, queue):
    while True:
        message = await queue.get()
        await write_file(filepath, handle_text(message))


async def read_msgs(host, port, queues):
    state = gui.ReadConnectionStateChanged
    queues['status_updates'].put_nowait(state.INITIATED)

    async with open_asyncio_connection(host, port) as rw_descriptor:
        reader, writer = rw_descriptor

        queues['status_updates'].put_nowait(state.ESTABLISHED)

        while True:
            data = await reader.readline()

            message = data.decode()
            queues['messages'].put_nowait(message)
            queues['saving'].put_nowait(message),
            queues['watchdog'].put_nowait('Connection is alive. Source: New message in chat')


if __name__ == '__main__':
    load_dotenv()
    account_hash_ = os.getenv('TOKEN')

    asyncio.run(main(account_hash_))
