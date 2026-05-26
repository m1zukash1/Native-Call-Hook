# Android Native Call Hooking for Encrypted Libraries

A proof-of-concept Android system that intercepts native `dlopen()` calls and reroutes them to a custom proxy function. This work originated from R&D work on a commercial Android application security product that I later decided to turn into a bachelor’s thesis.

---

## Overview

Some multi-platform frameworks like Flutter and .NET MAUI package user code inside the Android application as a separate `.so` library, for example `libapp.so`, and under the hood the corresponding platform VM loads this user code:

```
Java / ART
    ↓ initializes
libflutter.so
    ↓ loads
libapp.so
```

This creates a simple problem: one native library loads another native library without ever going through the Java layer. This becomes an issue if we want to encrypt `libapp.so`, because where and how do we place the decryption logic inside the application?

Using [ByteHook](https://github.com/bytedance/bhook), a PLT hooking library, it is possible to initialize a hook on functions such as `__loader_dlopen` and reroute them to a custom proxy function. This proxy function then acts as the decryption point for encrypted libraries like `libapp.so` or any other native library loaded by another native library.

Under the hood, Flutter loads `libapp.so` through `dlopen()`. However, for interception, it is more reliable to hook Android's internal `__loader_dlopen` entry point directly, because Bionic's exported `dlopen()` function is only a public wrapper that forwards the request to `__loader_dlopen()` together with the caller address. This makes `__loader_dlopen` a lower-level and more central interception point. It captures native library loads closer to the Android dynamic linker itself, including loads triggered by native runtimes such as Flutter.

Other frameworks use calls such as `android_dlopen_ext` in which case you should hook `__loader_android_dlopen_ext`.

## What this is and isn't

This is a proof of concept for the interception and in-memory loading pipeline, not a production-ready protection system. The XOR encryption with a hardcoded key is intentionally trivial. It keeps the crypto code out of the way so the interesting part (the hooking, routing, and memfd-backed loading) stays readable. A real deployment would swap in proper cryptography and key management without touching the interception logic.

## Fair warning

The source code was written alongside my bachelor's thesis. Some comments, error paths, and structure choices exist to satisfy academic requirements rather than engineering ones. The core mechanism is real though.