#include <jni.h>
#include "test_harness.h"

extern "C" {

JNIEXPORT void JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHookTestHarness_benchmarkDecryptPipeline(
        JNIEnv *env, jclass clazz, jstring path, jint iterations) {
    const char* pathStr = env->GetStringUTFChars(path, nullptr);
    benchmarkDecryptPipeline(pathStr, iterations);
    env->ReleaseStringUTFChars(path, pathStr);
}

JNIEXPORT void JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHookTestHarness_benchmarkHookOverhead(
        JNIEnv *env, jclass clazz, jint iterations) {
    benchmarkHookOverhead(iterations);
}

JNIEXPORT void JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHookTestHarness_testLoadFromPath(
        JNIEnv *env, jclass clazz, jstring path) {
    const char* pathStr = env->GetStringUTFChars(path, nullptr);
    testLoadFromPath(pathStr);
    env->ReleaseStringUTFChars(path, pathStr);
}

JNIEXPORT void JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHookTestHarness_testRepeatedLoad(
        JNIEnv *env, jclass clazz) {
    testRepeatedLoad();
}

JNIEXPORT void JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_NativeCallHookTestHarness_testConcurrentLoad(
        JNIEnv *env, jclass clazz, jint numThreads) {
    testConcurrentLoad(numThreads);
}

}
