#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import sys
import os
from Crypto import Random
from Crypto.Cipher import AES

FILE_PATH = os.path.realpath(__file__)
BIN_PATH = os.path.split(FILE_PATH)[0]
#CONFIG_PATH = os.path.split(BIN_PATH)[0] + '\conf\\auth.xml'
#print CONFIG_PATH

# 加密函数
def encrypt(plainPassword):
    def pad(s):
        x = AES.block_size - len(s) % AES.block_size
        return s + (chr(x) * x)
    paddedPassword = pad(plainPassword)
    iv = Random.OSRNG.new().read(AES.block_size)
    key = Random.OSRNG.new().read(32)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encryptedPassword = base64.b64encode(iv + cipher.encrypt(paddedPassword) + key)
    return encryptedPassword

# 解密函数
def decrypt(encryptedPassword):
    base64Decoded = base64.b64decode(encryptedPassword)
    unpad = lambda s: s[:-(s[-1])]
    iv = base64Decoded[:AES.block_size]
    key = base64Decoded[-32:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plainPassword = unpad(cipher.decrypt(base64Decoded[:-32]))[AES.block_size:]
    return plainPassword


if __name__ == '__main__':
    #print sys.argv
    #print len(sys.argv)
    if len(sys.argv) == 3:
        if sys.argv[1] == '-e':
            print(encrypt(sys.argv[2]))
        elif sys.argv[1] == '-d':
            print(decrypt(sys.argv[2]))
