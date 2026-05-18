#include "test_harness.h"
#include "nativecallhook.h"
#include <android/log.h>
#include <cmath>
#include <ctime>
#include <dlfcn.h>
#include <fstream>
#include <thread>
#include <unistd.h>
#include <vector>
#include <sys/syscall.h>
#include <linux/memfd.h>

#define LOG_TAG "NATIVECALLHOOK"
#define XOR_KEY 0x69

static double vec_mean(const std::vector<long>& v) {
    double s = 0;
    for (auto x : v) s += x;
    return s / v.size();
}

static double vec_stddev(const std::vector<long>& v) {
    double m = vec_mean(v);
    double var = 0;
    for (auto x : v) var += (x - m) * (x - m);
    return std::sqrt(var / v.size());
}

static int create_memfd_bench(const char* name) {
#ifdef __NR_memfd_create
    return syscall(__NR_memfd_create, name, MFD_CLOEXEC);
#else
    return memfd_create(name, MFD_CLOEXEC);
#endif
}

void benchmarkDecryptPipeline(const char* path, int iterations) {
    std::vector<long> read_us, decrypt_us, memfd_us, total_us;
    size_t file_size = 0;

    for (int i = 0; i < iterations; i++) {
        struct timespec t0, t1, t2, t3;

        clock_gettime(CLOCK_MONOTONIC, &t0);
        std::ifstream file_in(path, std::ios::binary);
        if (!file_in.is_open()) {
            __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                "BENCHMARK: cannot open %s", path);
            return;
        }
        std::vector<uint8_t> data(
            (std::istreambuf_iterator<char>(file_in)),
             std::istreambuf_iterator<char>());
        file_in.close();
        clock_gettime(CLOCK_MONOTONIC, &t1);

        if (i == 0) file_size = data.size();

        for (auto& b : data) b ^= XOR_KEY;
        clock_gettime(CLOCK_MONOTONIC, &t2);

        int fd = create_memfd_bench("benchmark");
        if (fd < 0) {
            __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                "BENCHMARK: memfd_create failed");
            return;
        }
        ftruncate(fd, static_cast<off_t>(data.size()));
        write(fd, data.data(), data.size());
        close(fd);
        clock_gettime(CLOCK_MONOTONIC, &t3);

        auto us = [](const struct timespec& a, const struct timespec& b) -> long {
            return (a.tv_sec - b.tv_sec) * 1000000L +
                   (a.tv_nsec - b.tv_nsec) / 1000;
        };

        read_us.push_back(us(t1, t0));
        decrypt_us.push_back(us(t2, t1));
        memfd_us.push_back(us(t3, t2));
        total_us.push_back(us(t3, t0));
    }

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
        "BENCHMARK: size=%zu iter=%d "
        "read=%.0f+/-%.0f decrypt=%.0f+/-%.0f "
        "memfd_write=%.0f+/-%.0f total=%.0f+/-%.0f (us)",
        file_size, iterations,
        vec_mean(read_us), vec_stddev(read_us),
        vec_mean(decrypt_us), vec_stddev(decrypt_us),
        vec_mean(memfd_us), vec_stddev(memfd_us),
        vec_mean(total_us), vec_stddev(total_us));
}

void benchmarkHookOverhead(int iterations) {
    struct timespec t0, t1;

    void* warmup = dlopen("libliba.so", RTLD_NOW);
    if (warmup) dlclose(warmup);

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < iterations; i++) {
        void* handle = dlopen("libliba.so", RTLD_NOW);
        if (handle) dlclose(handle);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);

    long total_ns = (t1.tv_sec - t0.tv_sec) * 1000000000L +
                    (t1.tv_nsec - t0.tv_nsec);
    long per_call_ns = total_ns / iterations;

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
        "OVERHEAD: iter=%d total_ns=%ld per_call_ns=%ld",
        iterations, total_ns, per_call_ns);
}

void testLoadFromPath(const char* path) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
        "FAILSAFE_TEST: attempting load from: %s", path);
    void* handle = load_decrypted_library(path, RTLD_LAZY);
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
        "FAILSAFE_TEST: result=%p (expected null for error case)", handle);
}

void testRepeatedLoad() {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
        "ROBUSTNESS: --- sequential repeated load (5 calls) ---");
    for (int i = 0; i < 5; i++) {
        void* handle = dlopen("liblibb.so", RTLD_LAZY);
        __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
            "ROBUSTNESS: sequential #%d handle=%p dlerror=%s",
            i + 1, handle, handle ? "(none)" : dlerror());
    }
}

void testConcurrentLoad(int num_threads) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
        "ROBUSTNESS: --- concurrent load (%d threads) ---", num_threads);
    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; i++) {
        threads.emplace_back([i]() {
            void* handle = dlopen("liblibb.so", RTLD_LAZY);
            __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
                "ROBUSTNESS: thread %d handle=%p dlerror=%s",
                i, handle, handle ? "(none)" : dlerror());
        });
    }
    for (auto& t : threads) t.join();
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
        "ROBUSTNESS: all %d threads completed", num_threads);
}
