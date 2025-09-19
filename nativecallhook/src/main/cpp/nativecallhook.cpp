#include "nativecallhook.h"
#include <android/log.h>
#include <string>

std::string getHelloWorldMessage() {
    return "Hello World from Native Call Hook Library!";
}

void logMessage(const std::string& message) {
    __android_log_print(ANDROID_LOG_DEBUG, "NativeCallHook", "%s", message.c_str());
}