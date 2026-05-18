cmake_minimum_required(VERSION 3.22.1)

project("nativecallhook")

find_package(bytehook REQUIRED CONFIG)

add_library(${CMAKE_PROJECT_NAME} SHARED
    nativecallhook.cpp
    jni_bridge.cpp
    test_harness.cpp
    jni_bridge_test.cpp
)

target_link_libraries(${CMAKE_PROJECT_NAME}
    android
    log
    dl
    bytehook::bytehook
)

# Export symbols for bytehook to work properly (helps with INITERR_SYM on Android 10+)
# Also align LOAD segments to 16 KB for Android 15+ compatibility
target_link_options(${CMAKE_PROJECT_NAME} PRIVATE "-Wl,--export-dynamic" "-Wl,-z,max-page-size=16384")

