#!/usr/bin/env python3
"""
Automated test runner for Native-Call-Hook bachelor thesis.
Runs tests on a connected ADB device and collects outputs for the thesis.

Usage:
    python tests/run_tests.py --serial <DEVICE_SERIAL>
"""
import argparse
import os
import subprocess
import sys
import time

PACKAGE = "lt.vilniustech.ezukauskas.nativecallhook"
ACTIVITY = f"{PACKAGE}/.MainActivity"
TEST_ACTIVITY = f"{PACKAGE}/.TestActivity"
APK_PATH = os.path.join("app", "build", "outputs", "apk", "debug", "app-debug.apk")
OUTPUT_DIR = os.path.join("tests", "outputs")
LOG_TAG = "NATIVECALLHOOK"

# Source paths (relative to repo root)
NATIVECALLHOOK_CPP = os.path.join(
    "nativecallhook", "src", "main", "cpp", "nativecallhook.cpp"
)
MAINACTIVITY_JAVA = os.path.join(
    "app", "src", "main", "java", "lt", "vilniustech",
    "ezukauskas", "nativecallhook", "MainActivity.java"
)


def adb(serial, *args, check=True, timeout=30):
    """Run an adb command and return stdout."""
    cmd = ["adb", "-s", serial] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=timeout, check=check)
    return result.stdout.strip()


def adb_shell(serial, shell_cmd, check=True, timeout=30):
    """Run a shell command on the device."""
    return adb(serial, "shell", shell_cmd, check=check, timeout=timeout)


def save(filename, content):
    """Save content to the outputs directory."""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  -> Saved {path}")


def force_stop(serial):
    """Force stop the app."""
    adb_shell(serial, f"am force-stop {PACKAGE}", check=False)
    time.sleep(1)


def start_app(serial):
    """Start the main activity and wait for native init to complete."""
    adb_shell(serial, f"am start -n {ACTIVITY} -W")
    time.sleep(3)


def clear_logcat(serial):
    """Clear logcat buffer."""
    adb(serial, "logcat", "-c")


def capture_logcat(serial, tag=LOG_TAG, timeout=5):
    """Capture logcat for a given tag."""
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "logcat", "-d", f"{tag}:V", "*:S"],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "(logcat capture timed out)"


def get_lib_dir(serial):
    """Discover the extracted native library directory on device."""
    pm_output = adb_shell(serial, f"pm path {PACKAGE}")
    apk_path = pm_output.replace("package:", "")
    app_dir = apk_path.rsplit("/", 1)[0]  # strip /base.apk
    for abi_dir in ["lib/arm64", "lib/arm64-v8a"]:
        candidate = f"{app_dir}/{abi_dir}"
        check = adb_shell(serial, f"ls {candidate}/liblibb.so 2>/dev/null", check=False)
        if "liblibb.so" in check:
            return candidate
    return None


def gradle_build():
    """Run Gradle assembleDebug and return (success, output)."""
    result = subprocess.run(
        ["cmd", "/c", "gradlew.bat", "assembleDebug"],
        capture_output=True, text=True, timeout=180
    )
    success = result.returncode == 0
    output = result.stdout + "\n" + result.stderr
    return success, output


def read_file_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ──────────────────────────────────────────────────────────────────────
# 4.1 Test environment
# ──────────────────────────────────────────────────────────────────────
def test_environment(serial):
    print("\n[4.1] Collecting test environment info...")
    props = {
        "Model": adb_shell(serial, "getprop ro.product.model"),
        "Android version": adb_shell(serial, "getprop ro.build.version.release"),
        "API level": adb_shell(serial, "getprop ro.build.version.sdk"),
        "Build ID": adb_shell(serial, "getprop ro.build.display.id"),
        "Security patch": adb_shell(serial, "getprop ro.build.version.security_patch"),
        "ABI": adb_shell(serial, "getprop ro.product.cpu.abilist"),
        "Kernel": adb_shell(serial, "uname -r"),
    }
    lines = [f"{k}: {v}" for k, v in props.items()]
    out = "\n".join(lines)
    save("4_1_environment.txt", out)
    print(out)
    return props


# ──────────────────────────────────────────────────────────────────────
# 4.2 Build-time encryption verification
# ──────────────────────────────────────────────────────────────────────
def test_encryption_verification(serial, lib_dir):
    print("\n[4.2] Build-time encryption verification...")

    hex_encrypted = adb_shell(serial, f"xxd -l 16 {lib_dir}/liblibb.so")
    hex_normal = adb_shell(serial, f"xxd -l 16 {lib_dir}/libliba.so")
    hex_hook = adb_shell(serial, f"xxd -l 16 {lib_dir}/libnativecallhook.so")

    def has_elf_magic(hex_line):
        normalized = hex_line.replace(" ", "").lower()
        return "7f454c46" in normalized

    liba_elf = has_elf_magic(hex_normal)
    libb_elf = has_elf_magic(hex_encrypted)
    hook_elf = has_elf_magic(hex_hook)

    out = (
        f"Library directory: {lib_dir}\n\n"
        f"--- libliba.so (normal, unprotected) first 16 bytes ---\n"
        f"{hex_normal}\n"
        f"Valid ELF: {liba_elf}\n\n"
        f"--- liblibb.so (encrypted, protected) first 16 bytes ---\n"
        f"{hex_encrypted}\n"
        f"Valid ELF: {libb_elf}\n\n"
        f"--- libnativecallhook.so (hook library) first 16 bytes ---\n"
        f"{hex_hook}\n"
        f"Valid ELF: {hook_elf}\n\n"
        f"RESULT: liblibb.so does {'NOT ' if not libb_elf else ''}contain ELF magic.\n"
        f"The encrypted first bytes (16 2c 25 2f) correspond to 7f 45 4c 46 XOR 0x69.\n"
    )
    save("4_2_encryption_verification.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# 4.3 Hook installation
# ──────────────────────────────────────────────────────────────────────
def test_hook_installation(serial):
    print("\n[4.3] Hook installation verification...")
    force_stop(serial)
    clear_logcat(serial)
    start_app(serial)

    logs = capture_logcat(serial)

    hook_lines = [l for l in logs.splitlines()
                  if any(kw in l for kw in [
                      "dlopen hook installed",
                      "bytehook_init",
                      "hooks installed",
                      "NativeCallHook active"
                  ])]

    out = (
        f"--- Hook installation log lines ---\n"
        + ("\n".join(hook_lines) if hook_lines else "(none found)")
        + f"\n\n--- Full NATIVECALLHOOK logcat ---\n{logs}\n"
    )
    save("4_3_hook_installation.txt", out)
    print(out)
    return logs


# ──────────────────────────────────────────────────────────────────────
# 4.4 Unprotected library passthrough
# ──────────────────────────────────────────────────────────────────────
def test_unprotected_passthrough(serial, logs):
    print("\n[4.4] Unprotected library passthrough...")

    intercepted_liba = [l for l in logs.splitlines()
                        if "Intercepted" in l and "liba" in l]
    intercepted_any = [l for l in logs.splitlines() if "Intercepted" in l]

    out = (
        f"--- All interception log lines ---\n"
        + ("\n".join(intercepted_any) if intercepted_any else "(none)")
        + f"\n\nInterception lines mentioning liba: {len(intercepted_liba)}\n"
    )
    if not intercepted_liba:
        out += "RESULT: libliba.so was NOT routed through decryption (correct behavior).\n"
    else:
        out += "WARNING: libliba.so was intercepted (unexpected).\n"

    out += f"\n--- Full logcat ---\n{logs}\n"
    save("4_4_unprotected_passthrough.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# 4.5 Protected library end-to-end load
# ──────────────────────────────────────────────────────────────────────
def test_protected_load(serial, logs):
    print("\n[4.5] Protected library end-to-end load...")

    keywords = [
        "Intercepted dlopen for encrypted library",
        "Loading encrypted library",
        "Successfully loaded decrypted library",
        "Invalid ELF",
        "memfd",
        "android_dlopen_ext",
    ]
    relevant = [l for l in logs.splitlines() if any(k in l for k in keywords)]

    success = any("Successfully loaded decrypted" in l for l in logs.splitlines())

    out = (
        f"--- Decryption pipeline log lines ---\n"
        + ("\n".join(relevant) if relevant else "(none found)")
        + f"\n\nEnd-to-end load successful: {success}\n"
        + f"\n--- Full logcat ---\n{logs}\n"
    )
    save("4_5_protected_load.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# 4.6 Native-to-native load coverage
# ──────────────────────────────────────────────────────────────────────
def test_native_to_native(serial, logs):
    print("\n[4.6] Native-to-native load coverage...")

    libb_lines = [l for l in logs.splitlines() if "LibB:" in l]
    liba_dlopen = [l for l in logs.splitlines()
                   if "Intercepted" in l and "liblibb" in l]

    out = (
        f"--- LibB output lines (proves call_logcat executed after decryption) ---\n"
        + ("\n".join(libb_lines) if libb_lines else "(none found)")
        + f"\n\n--- Interception of liblibb.so by liba's dlopen ---\n"
        + ("\n".join(liba_dlopen) if liba_dlopen else "(none found)")
        + f"\n\nNative-to-native chain successful: "
        + f"{'yes' if libb_lines else 'no'}\n"
        + f"\n--- Full logcat ---\n{logs}\n"
    )
    save("4_6_native_to_native.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# 4.7 Fail-safe behaviour (wrong decryption key)
# ──────────────────────────────────────────────────────────────────────
def test_failsafe(serial):
    print("\n[4.7] Fail-safe behaviour (wrong decryption key)...")

    original_cpp = read_file_text(NATIVECALLHOOK_CPP)

    modified_cpp = original_cpp.replace(
        "#define XOR_KEY 0x69",
        "#define XOR_KEY 0xAA  // WRONG KEY FOR TESTING"
    )

    if modified_cpp == original_cpp:
        print("  ERROR: Could not find XOR_KEY definition")
        save("4_7_failsafe.txt", "ERROR: XOR_KEY not found in source")
        return

    write_file_text(NATIVECALLHOOK_CPP, modified_cpp)
    print("  Modified XOR_KEY to 0xAA (wrong key)")

    try:
        print("  Building APK with wrong decryption key...")
        success, build_out = gradle_build()
        if not success:
            print(f"  Build failed")
            save("4_7_failsafe.txt", f"Build failed:\n{build_out[-1000:]}")
            return

        adb(serial, "install", "-r", APK_PATH)
        force_stop(serial)
        clear_logcat(serial)
        start_app(serial)

        logs = capture_logcat(serial)

        failsafe_lines = [l for l in logs.splitlines()
                          if any(k in l for k in [
                              "Invalid ELF", "Failed", "error",
                              "nullptr", "failed"
                          ])]

        elf_invalid = any("Invalid ELF" in l for l in logs.splitlines())
        success_load = any("Successfully loaded" in l for l in logs.splitlines())

        pid = adb_shell(serial, f"pidof {PACKAGE}", check=False)

        out = (
            f"Test: XOR_KEY changed from 0x69 to 0xAA (wrong key)\n"
            f"Expected: ELF magic validation fails, library not loaded, app survives\n\n"
            f"--- Fail-safe and error log lines ---\n"
            + ("\n".join(failsafe_lines) if failsafe_lines else "(none)")
            + f"\n\nELF validation failed: {elf_invalid}\n"
            + f"Library loaded successfully: {success_load}\n"
            + f"App process alive after failure: "
            + f"{'yes (PID ' + pid + ')' if pid else 'no'}\n"
            + f"\n--- Full logcat ---\n{logs}\n"
        )
        save("4_7_failsafe.txt", out)
        print(out)

    finally:
        write_file_text(NATIVECALLHOOK_CPP, original_cpp)
        print("  Restored original XOR_KEY (0x69)")

        print("  Rebuilding with correct key...")
        gradle_build()
        adb(serial, "install", "-r", APK_PATH)
        print("  Reinstalled correct APK")


# ──────────────────────────────────────────────────────────────────────
# 4.8 Load order enforcement (swapped static block)
# ──────────────────────────────────────────────────────────────────────
def test_load_order(serial):
    print("\n[4.8] Load order enforcement (swapped static block)...")

    original_java = read_file_text(MAINACTIVITY_JAVA)

    old_block = (
        '        NativeCallHook.initialize();\n'
        '        System.loadLibrary("liba");'
    )

    new_block = (
        '        System.loadLibrary("liba");\n'
        '        NativeCallHook.initialize();'
    )

    if old_block not in original_java:
        # Try without em-dash (in case file was changed)
        old_block_alt = old_block.replace("—", "-")
        if old_block_alt in original_java:
            old_block = old_block_alt
        else:
            # Debug: show what the static block actually looks like
            print("  WARNING: Static block pattern not found. Trying regex match...")
            import re
            m = re.search(r'(static\s*\{.*?})', original_java, re.DOTALL)
            if m:
                print(f"  Actual static block:\n{m.group(1)[:500]}")
            save("4_8_load_order.txt",
                 f"ERROR: Could not match static block pattern.\n"
                 f"Searched for:\n{old_block}\n\n"
                 f"File starts with:\n{original_java[:800]}")
            return

    swapped_java = original_java.replace(old_block, new_block)
    write_file_text(MAINACTIVITY_JAVA, swapped_java)
    print("  Modified MainActivity.java (swapped load order)")

    try:
        print("  Building APK with swapped order...")
        success, build_out = gradle_build()
        if not success:
            print(f"  Build failed")
            save("4_8_load_order.txt", f"Build failed:\n{build_out[-1000:]}")
            return

        adb(serial, "install", "-r", APK_PATH)
        force_stop(serial)
        clear_logcat(serial)
        start_app(serial)

        logs = capture_logcat(serial)

        failure_lines = [l for l in logs.splitlines()
                         if any(k in l for k in [
                             "Failed to load LibB", "dlopen failed",
                             "error", "Failed"
                         ])]
        success_lines = [l for l in logs.splitlines()
                         if "Successfully loaded decrypted" in l]
        libb_output = [l for l in logs.splitlines() if "LibB:" in l]

        pid = adb_shell(serial, f"pidof {PACKAGE}", check=False)

        out = (
            f'Test: System.loadLibrary("liba") called BEFORE NativeCallHook.initialize()\n'
            f"Expected: Hook not installed when liba tries dlopen(\"liblibb.so\"),\n"
            f"          so the encrypted file is passed to the real linker which rejects it.\n\n"
            f"--- Failure log lines ---\n"
            + ("\n".join(failure_lines) if failure_lines else "(none)")
            + f"\n\n--- Success lines ---\n"
            + ("\n".join(success_lines) if success_lines else "(none)")
            + f"\n\n--- LibB output ---\n"
            + ("\n".join(libb_output) if libb_output else "(none — LibB never executed)")
            + f"\n\nApp process alive: "
            + f"{'yes (PID ' + pid + ')' if pid else 'no'}\n"
            + f"\n--- Full logcat ---\n{logs}\n"
        )
        save("4_8_load_order.txt", out)
        print(out)

    finally:
        write_file_text(MAINACTIVITY_JAVA, original_java)
        print("  Restored original MainActivity.java")

        print("  Rebuilding with correct load order...")
        gradle_build()
        adb(serial, "install", "-r", APK_PATH)
        print("  Reinstalled correct APK")


# ──────────────────────────────────────────────────────────────────────
# 4.9 Performance benchmark (multi-size decryption pipeline)
# ──────────────────────────────────────────────────────────────────────
def test_benchmark(serial):
    print("\n[4.9] Performance benchmark (multi-size decryption pipeline)...")
    force_stop(serial)
    clear_logcat(serial)

    adb_shell(serial, f'am start -n {TEST_ACTIVITY} --es mode benchmark -W')
    # Wait for all benchmark iterations to finish (6 sizes × 10 iterations)
    time.sleep(20)

    logs = capture_logcat(serial, timeout=10)
    benchmark_lines = [l for l in logs.splitlines() if "BENCHMARK:" in l]

    out = (
        "Test: Decryption pipeline performance across file sizes\n"
        "Methodology: 10 iterations per size, measuring read + XOR-decrypt + memfd_write\n"
        "Sizes: 1KB, 10KB, 100KB, 1MB, 5MB, 10MB\n\n"
        "--- Benchmark results ---\n"
        + ("\n".join(benchmark_lines) if benchmark_lines else "(no benchmark output)")
        + f"\n\n--- Full logcat ---\n{logs}\n"
    )
    save("4_9_benchmark.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# 4.10 Fail-safe: missing file, empty file, truncated file
# ──────────────────────────────────────────────────────────────────────
def test_failsafe_extra(serial):
    print("\n[4.10] Fail-safe: missing / empty / truncated file...")
    force_stop(serial)
    clear_logcat(serial)

    adb_shell(serial, f'am start -n {TEST_ACTIVITY} --es mode test_failsafe -W')
    time.sleep(5)

    logs = capture_logcat(serial, timeout=5)
    failsafe_lines = [l for l in logs.splitlines()
                      if "FAILSAFE_TEST:" in l or "Failed to open" in l
                      or "Invalid ELF" in l]

    pid = adb_shell(serial, f"pidof {PACKAGE}", check=False)

    out = (
        "Test: Fail-safe behaviour for missing, empty, and truncated files\n"
        "Methodology: Direct calls to load_decrypted_library with invalid inputs\n"
        "Expected: Each call logs an error and returns nullptr, app survives\n\n"
        "--- Fail-safe log lines ---\n"
        + ("\n".join(failsafe_lines) if failsafe_lines else "(none)")
        + f"\n\nApp process alive: "
        + f"{'yes (PID ' + pid.strip() + ')' if pid.strip() else 'no'}\n"
        + f"\n--- Full logcat ---\n{logs}\n"
    )
    save("4_10_failsafe_extra.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# 4.11 Robustness (repeated and concurrent loads)
# ──────────────────────────────────────────────────────────────────────
def test_robustness(serial):
    print("\n[4.11] Robustness (repeated and concurrent loads)...")
    force_stop(serial)
    clear_logcat(serial)

    adb_shell(serial, f'am start -n {TEST_ACTIVITY} --es mode test_robustness -W')
    time.sleep(10)

    logs = capture_logcat(serial, timeout=5)
    robustness_lines = [l for l in logs.splitlines() if "ROBUSTNESS:" in l]

    pid = adb_shell(serial, f"pidof {PACKAGE}", check=False)

    out = (
        "Test: Robustness under repeated and concurrent encrypted library loads\n"
        "Methodology: 5 sequential dlopen calls + 4 concurrent threads\n"
        "Expected: All calls succeed or return cached handle, app survives\n\n"
        "--- Robustness log lines ---\n"
        + ("\n".join(robustness_lines) if robustness_lines else "(none)")
        + f"\n\nApp process alive: "
        + f"{'yes (PID ' + pid.strip() + ')' if pid.strip() else 'no'}\n"
        + f"\n--- Full logcat ---\n{logs}\n"
    )
    save("4_11_robustness.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# 4.12 Hook overhead measurement
# ──────────────────────────────────────────────────────────────────────
def test_hook_overhead(serial):
    print("\n[4.12] Hook overhead measurement...")
    force_stop(serial)
    clear_logcat(serial)

    adb_shell(serial, f'am start -n {TEST_ACTIVITY} --es mode test_overhead -W')
    time.sleep(5)

    logs = capture_logcat(serial, timeout=5)
    overhead_lines = [l for l in logs.splitlines() if "OVERHEAD:" in l]

    out = (
        "Test: Hook overhead for non-encrypted library dlopen calls\n"
        "Methodology: 1000 dlopen/dlclose cycles on libliba.so (non-encrypted)\n"
        "Expected: Minimal per-call overhead from is_encrypted_library() check\n\n"
        "--- Overhead results ---\n"
        + ("\n".join(overhead_lines) if overhead_lines else "(none)")
        + f"\n\n--- Full logcat ---\n{logs}\n"
    )
    save("4_12_hook_overhead.txt", out)
    print(out)


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Native-Call-Hook test runner")
    parser.add_argument("--serial", required=True, help="ADB device serial")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Native-Call-Hook Thesis Test Runner")
    print(f"Device: {args.serial}")
    print("=" * 60)

    lib_dir = get_lib_dir(args.serial)
    if not lib_dir:
        print("FATAL: Could not locate native library directory on device.")
        sys.exit(1)
    print(f"Library directory: {lib_dir}")

    props = test_environment(args.serial)
    test_encryption_verification(args.serial, lib_dir)
    full_logs = test_hook_installation(args.serial)
    test_unprotected_passthrough(args.serial, full_logs)
    test_protected_load(args.serial, full_logs)
    test_native_to_native(args.serial, full_logs)
    test_failsafe(args.serial)
    test_load_order(args.serial)
    test_benchmark(args.serial)
    test_failsafe_extra(args.serial)
    test_robustness(args.serial)
    test_hook_overhead(args.serial)

    print("\n" + "=" * 60)
    print(f"All tests complete. Outputs saved to {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
