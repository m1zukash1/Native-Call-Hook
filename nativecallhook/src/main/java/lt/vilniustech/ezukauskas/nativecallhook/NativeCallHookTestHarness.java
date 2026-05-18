package lt.vilniustech.ezukauskas.nativecallhook;

public class NativeCallHookTestHarness {

    public static native void benchmarkDecryptPipeline(String path, int iterations);

    public static native void benchmarkHookOverhead(int iterations);

    public static native void testLoadFromPath(String path);

    public static native void testRepeatedLoad();

    public static native void testConcurrentLoad(int numThreads);
}
