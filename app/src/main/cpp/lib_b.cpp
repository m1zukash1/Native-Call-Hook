#include <android/log.h>

#define LOG_TAG "NATIVECALLHOOK"

extern "C" {

    /**
     * Simple exported function used to verify that the encrypted library
     * was correctly decrypted and loaded at runtime.
     */
    void call_logcat(const char* message) {
        __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "LibB: %s", message);
    }

}
