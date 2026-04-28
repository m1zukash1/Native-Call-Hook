#include <jni.h>
#include <dlfcn.h>
#include <android/log.h>

#define LOG_TAG "NATIVECALLHOOK"

extern "C" {

    typedef void (*call_logcat_func_t)(const char*);

    /**
     * Demonstrates native-to-native library loading.
     * Calls dlopen("liblibb.so") which will be intercepted by the hook
     * if liblibb.so is in the encrypted library list.
     */
    JNIEXPORT void JNICALL
    Java_lt_vilniustech_ezukauskas_nativecallhook_MainActivity_loadEncryptedLibrary(JNIEnv *env, jobject thiz) {
        void* lib_b_handle = dlopen("liblibb.so", RTLD_LAZY);

        if (!lib_b_handle) {
            __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "LibA: Failed to load LibB: %s", dlerror());
            return;
        }

        call_logcat_func_t call_logcat = (call_logcat_func_t)dlsym(lib_b_handle, "call_logcat");

        if (!call_logcat) {
            __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "LibA: Failed to find call_logcat: %s", dlerror());
            dlclose(lib_b_handle);
            return;
        }

        call_logcat("Hello from LibB, called by LibA after decryption");

        dlclose(lib_b_handle);
    }

}
