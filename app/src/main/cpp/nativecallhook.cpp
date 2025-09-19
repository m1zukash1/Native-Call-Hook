#include <jni.h>
#include <string>

extern "C" JNIEXPORT jstring JNICALL
Java_lt_vilniustech_ezukauskas_nativecallhook_MainActivity_getHelloWorld(JNIEnv *env, jobject /* this */) {
    std::string hello = "Hello World from C++!";
    return env->NewStringUTF(hello.c_str());
}