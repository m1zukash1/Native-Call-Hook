#include <jni.h>
#include "nativecallhook.h"

extern "C" {

JNIEXPORT jstring JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHook_getHelloWorld(JNIEnv *env, jclass clazz) {
    std::string message = getHelloWorldMessage();
    logMessage(message);
    return env->NewStringUTF(message.c_str());
}

JNIEXPORT void JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHook_logMessage(JNIEnv *env, jclass clazz, jstring message) {
    const char* nativeMessage = env->GetStringUTFChars(message, 0);
    logMessage(std::string(nativeMessage));
    env->ReleaseStringUTFChars(message, nativeMessage);
}

}