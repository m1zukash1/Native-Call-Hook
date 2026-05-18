#include "nativecallhook.h"
#include <android/log.h>
#include <android/dlext.h>
#include <string>
#include <cstring>
#include <cerrno>
#include <fstream>
#include <vector>
#include <dlfcn.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <linux/memfd.h>
#include "bytehook.h"

#define LOG_TAG "NATIVECALLHOOK"
#define XOR_KEY 0x69

// List of encrypted libraries
static const char* ENCRYPTED_LIBS[] = {
    "liblibb.so",
    nullptr
};

// Store memfd for loaded libraries to prevent premature closure
static int g_memfd_liblibb = -1;

/**
 * Check if a library filename is in the encrypted list
 */
static bool is_encrypted_library(const char* filename) {
    if (!filename) return false;

    for (int i = 0; ENCRYPTED_LIBS[i]; i++) {
        if (strstr(filename, ENCRYPTED_LIBS[i])) {
            return true;
        }
    }
    return false;
}

/**
 * Get the full path of a library by using dladdr on a known function
 * Assumes extractNativeLibs=true and all libs are in the same directory
 */
static std::string get_library_full_path(const char* filename) {
    Dl_info info;
    if (dladdr(reinterpret_cast<void*>(&get_library_full_path), &info) && info.dli_fname) {
        std::string lib_path(info.dli_fname);
        size_t pos = lib_path.find_last_of('/');
        if (pos != std::string::npos) {
            return lib_path.substr(0, pos + 1) + filename;
        }
    }
    return filename;
}

/**
 * Create an anonymous in-memory file using memfd_create
 */
static int create_memfd(const char* name) {
#ifdef __NR_memfd_create
    return syscall(__NR_memfd_create, name, MFD_CLOEXEC);
#else
    return memfd_create(name, MFD_CLOEXEC);
#endif
}

void* load_decrypted_library(const char* original_path, int flags) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
                       "Loading encrypted library: %s", original_path);

    // Read encrypted file from disk
    std::ifstream file_in(original_path, std::ios::binary);
    if (!file_in.is_open()) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                           "Failed to open encrypted file: %s", original_path);
        return nullptr;
    }

    std::vector<uint8_t> data((std::istreambuf_iterator<char>(file_in)),
                              std::istreambuf_iterator<char>());
    file_in.close();

    // Decrypt in memory using XOR cipher
    for (auto& byte : data) {
        byte ^= XOR_KEY;
    }

    // Validate ELF magic bytes after decryption
    if (data.size() < 4 ||
        data[0] != 0x7f || data[1] != 'E' || data[2] != 'L' || data[3] != 'F') {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                           "Invalid ELF magic after decryption");
        return nullptr;
    }

    // Create anonymous in-memory file and write decrypted content
    int fd = create_memfd("decrypted_lib");
    if (fd < 0) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                           "memfd_create failed: %s", strerror(errno));
        return nullptr;
    }

    if (ftruncate(fd, static_cast<off_t>(data.size())) < 0) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                           "ftruncate failed: %s", strerror(errno));
        close(fd);
        return nullptr;
    }

    ssize_t written = write(fd, data.data(), data.size());
    if (written != static_cast<ssize_t>(data.size())) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                           "Write to memfd failed: written=%zd, expected=%zu",
                           written, data.size());
        close(fd);
        return nullptr;
    }

    // Load the decrypted library directly from the memfd
    android_dlextinfo extinfo = {};
    extinfo.flags = ANDROID_DLEXT_USE_LIBRARY_FD;
    extinfo.library_fd = fd;
    extinfo.library_fd_offset = 0;

    void* handle = android_dlopen_ext(original_path, flags, &extinfo);

    if (handle) {
        g_memfd_liblibb = fd;  // Keep fd open for library lifetime
        __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
                           "Successfully loaded decrypted library from memfd");
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                           "android_dlopen_ext failed: %s", dlerror());
        close(fd);
    }

    return handle;
}

/**
 * Hooked dlopen - intercepts library loading and decrypts encrypted libraries
 */
static void* hooked_dlopen(const char* filename, int flags) {
    BYTEHOOK_STACK_SCOPE();

    if (filename && is_encrypted_library(filename)) {
        __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
                           "Intercepted dlopen for encrypted library: %s", filename);

        std::string full_path = get_library_full_path(filename);
        return load_decrypted_library(full_path.c_str(), flags);
    }

    return BYTEHOOK_CALL_PREV(hooked_dlopen, filename, flags);
}

/**
 * Library constructor — runs automatically when libnativecallhook.so is loaded.
 * Initializes ByteHook and installs the PLT hook on __loader_dlopen.
 */
__attribute__((constructor)) static void init_hook() {
    int result = bytehook_init(BYTEHOOK_MODE_AUTOMATIC, true);
    if (result != BYTEHOOK_STATUS_CODE_OK) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                           "bytehook_init failed: %d", result);
        return;
    }

    bytehook_stub_t stub = bytehook_hook_all(
        nullptr,
        "__loader_dlopen",
        (void*)hooked_dlopen,
        nullptr,
        nullptr
    );

    if (stub == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to hook __loader_dlopen");
        return;
    }

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "dlopen hook installed successfully");
}

std::string getStatus() {
    return "NativeCallHook active — hooks installed";
}

void nch_log(const std::string& message) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "%s", message.c_str());
}

