#ifndef TEST_HARNESS_H
#define TEST_HARNESS_H

void benchmarkDecryptPipeline(const char* path, int iterations);
void benchmarkHookOverhead(int iterations);
void testLoadFromPath(const char* path);
void testRepeatedLoad();
void testConcurrentLoad(int num_threads);

#endif // TEST_HARNESS_H
