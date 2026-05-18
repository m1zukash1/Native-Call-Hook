#ifndef NATIVECALLHOOK_H
#define NATIVECALLHOOK_H

#include <string>

std::string getStatus();
void nch_log(const std::string& message);

void* load_decrypted_library(const char* original_path, int flags);

#endif // NATIVECALLHOOK_H