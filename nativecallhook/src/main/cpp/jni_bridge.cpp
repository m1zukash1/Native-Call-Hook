#include <jni.h>
#include "nativecallhook.h"
#include <android/log.h>

#define LOG_TAG "NATIVECALLHOOK"

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    return JNI_VERSION_1_6;
}

extern "C" {

JNIEXPORT jboolean JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHook_initialize(JNIEnv *env, jclass clazz) {
    // Hook is installed by the C++ constructor (init_hook) at library load time.
    // This method exists so the Java layer can trigger the library load via System.loadLibrary.
    return JNI_TRUE;
}

JNIEXPORT jstring JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHook_getStatus(JNIEnv *env, jclass clazz) {
    std::string status = getStatus();
    return env->NewStringUTF(status.c_str());
}

JNIEXPORT void JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHook_log(JNIEnv *env, jclass clazz, jstring message) {
    const char* nativeMessage = env->GetStringUTFChars(message, nullptr);
    log(std::string(nativeMessage));
    env->ReleaseStringUTFChars(message, nativeMessage);
}

}