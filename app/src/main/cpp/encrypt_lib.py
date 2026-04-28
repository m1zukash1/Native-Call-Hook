#!/usr/bin/env python3
"""
Library Encryption Script
Encrypts liblibb.so using XOR encryption after build.
This script is called automatically by CMake as a POST_BUILD step.

The XOR key (0x69) must match the key in nativecallhook.cpp for decryption.
"""
import os
import sys

def xor_encrypt(file_path, key):
    """Encrypt/decrypt a file using XOR cipher with the given key."""
    with open(file_path, 'rb') as f:
        data = f.read()

    encrypted_data = bytearray([b ^ key for b in data])

    with open(file_path, 'wb') as f:
        f.write(encrypted_data)

    print(f"[ENCRYPT] {file_path} encrypted with key 0x{key:02X}")

if __name__ == "__main__":
    build_dir = os.getcwd()
    lib_path = os.path.join(build_dir, 'liblibb.so')

    # XOR encryption key - must match XOR_KEY in nativecallhook.cpp
    key = 0x69

    if not os.path.exists(lib_path):
        print(f"[ERROR] Library not found: {lib_path}")
        sys.exit(1)

    xor_encrypt(lib_path, key)
