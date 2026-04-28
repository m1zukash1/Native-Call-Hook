cmake_minimum_required(VERSION 3.22.1)

project("nativecallhook")

# 16 KB page alignment required for Android 15+ (API 35+) devices
add_link_options("-Wl,-z,max-page-size=16384")

# Demo library A: loads liblibb.so at runtime via dlopen
add_library(liba SHARED lib_a.cpp)
target_link_libraries(liba android log dl)

# Demo library B: encrypted at build time, decrypted at runtime by the hook
add_library(libb SHARED lib_b.cpp)
target_link_libraries(libb android log)

# Post-build step: XOR-encrypt liblibb.so so the hook can demonstrate decryption
add_custom_command(TARGET libb POST_BUILD
        COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/encrypt_lib.py
        WORKING_DIRECTORY $<TARGET_FILE_DIR:libb>
        COMMENT "Encrypting liblibb.so after build"
)
