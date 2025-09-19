#include <android/log.h>

extern "C" {
    
    void call_logcat(const char* message) {
        __android_log_print(ANDROID_LOG_DEBUG, "NativeCallHook", "LibB: %s", message);
    }
    
}
