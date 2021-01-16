import asyncio
import tkinter as tk

from config import HOST, WRITE_PORT
from write_to_minechat import register


class Block:
    def __init__(self, master, func):
        self.ent = tk.Entry(master, width=20)
        self.but = tk.Button(master, text='Зарегистрироваться')
        self.lab = tk.Label(master, width=40, bg='black', fg='white')
        self.but['command'] = eval('self.' + func)
        self.ent.pack()
        self.but.pack()
        self.lab.pack()

    def register(self):
        nickname = self.ent.get()

        account_dict = asyncio.run(
            register(HOST, WRITE_PORT, nickname)
        )

        register_data = 'NICKNAME={}\nTOKEN={}\n'.format(account_dict['nickname'], account_dict['account_hash'])

        with open('.env', 'w') as fd:
            fd.write(register_data)

        self.lab['text'] = register_data


if __name__ == '__main__':
    root = tk.Tk()

    Block(root, 'register')

    root.mainloop()
