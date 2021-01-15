import asyncio
from contextlib import asynccontextmanager

from heandler import handle_text
from utils import write_file

delay = 0
error_count = 0


@asynccontextmanager
async def open_asyncio_connection(host, port, filename=None):
    global error_count, delay

    try:
        reader, writer = await asyncio.open_connection(host, port)

        if error_count > 0:

            if filename is not None:
                await write_file(filename, handle_text('Установлено соединение.'))

        error_count = 0
        delay = 0

        yield reader, writer

    except asyncio.CancelledError:
        error_count += 1

        if error_count <= 2:
            message = handle_text('Нет соединения. Повторная попытка.')

        else:
            delay = 3
            message = handle_text('Нет соединения. Повторная попытка через 3 сек.')

        if filename is not None:
            await write_file(filename, message)

        await asyncio.sleep(delay)

        raise

    except ConnectionResetError:
        if filename is not None:
            await write_file(filename, handle_text('Удаленный хост принудительно разорвал существующее подключение.'))


    finally:
        if filename is not None:
            await write_file(filename, handle_text('Cоединение закрыто.'))

        writer.close()
