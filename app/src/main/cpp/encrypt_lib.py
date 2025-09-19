import os
import sys

def xor_encrypt(file_path, key):
    with open(file_path, 'rb') as f:
        data = f.read()

    encrypted_data = bytearray([b ^ key for b in data])

    with open(file_path, 'wb') as f:
        f.write(encrypted_data)

if __name__ == "__main__":
    build_dir = os.getcwd()
    lib_path = os.path.join(build_dir, 'liblibb.so')

    key = 0x69
    xor_encrypt(lib_path, key)
