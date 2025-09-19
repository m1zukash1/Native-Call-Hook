#include <jni.h>
#include <dlfcn.h>
#include <android/log.h>
#include <string>

extern "C" {

    typedef void (*call_logcat_func_t)(const char*);

    JNIEXPORT void JNICALL
    Java_lt_vilniustech_ezukauskas_nativecallhook_MainActivity_testLibraryLoading(JNIEnv *env, jobject thiz) {
        __android_log_print(ANDROID_LOG_DEBUG, "NativeCallHook", "LibA: Starting library loading test");
        
        void* lib_b_handle = dlopen("liblibb.so", RTLD_LAZY);
        
        if (!lib_b_handle) {
            __android_log_print(ANDROID_LOG_ERROR, "NativeCallHook", "LibA: Failed to load LibB: %s", dlerror());
            return;
        }
        
        __android_log_print(ANDROID_LOG_DEBUG, "NativeCallHook", "LibA: Successfully loaded LibB");
        
        call_logcat_func_t call_logcat = (call_logcat_func_t)dlsym(lib_b_handle, "call_logcat");
        
        if (!call_logcat) {
            __android_log_print(ANDROID_LOG_ERROR, "NativeCallHook", "LibA: Failed to find call_logcat function: %s", dlerror());
            dlclose(lib_b_handle);
            return;
        }
        
        __android_log_print(ANDROID_LOG_DEBUG, "NativeCallHook", "LibA: Found call_logcat function, calling it...");
        
        call_logcat("Hello from LibB called by LibA!");
        
        __android_log_print(ANDROID_LOG_DEBUG, "NativeCallHook", "LibA: Successfully called LibB function");
        
        dlclose(lib_b_handle);
    }
    
}
