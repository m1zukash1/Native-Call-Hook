#include <jni.h>
#include "nativecallhook.h"

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    return JNI_VERSION_1_6;
}

extern "C" {

JNIEXPORT jboolean JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHook_initialize(JNIEnv *env, jclass clazz) {
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
    nch_log(std::string(nativeMessage));
    env->ReleaseStringUTFChars(message, nativeMessage);
}

}