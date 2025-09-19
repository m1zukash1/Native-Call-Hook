cmake_minimum_required(VERSION 3.22.1)

project("nativecallhook")

add_library(liba SHARED lib_a.cpp)

add_library(libb SHARED lib_b.cpp)

target_link_libraries(liba android log dl)
target_link_libraries(libb android log)

add_custom_command(TARGET libb POST_BUILD
        COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/encrypt_lib.py
        WORKING_DIRECTORY $<TARGET_FILE_DIR:libb>
        COMMENT "Encrypting libnativelibtwo.so after build"
)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/nativecallhook.cpp")
    add_library(${CMAKE_PROJECT_NAME} SHARED nativecallhook.cpp)
    target_link_libraries(${CMAKE_PROJECT_NAME} android log)
endif()
