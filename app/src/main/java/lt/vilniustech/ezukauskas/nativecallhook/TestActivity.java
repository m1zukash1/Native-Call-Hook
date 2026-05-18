package lt.vilniustech.ezukauskas.nativecallhook;

import android.os.Bundle;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

import androidx.appcompat.app.AppCompatActivity;

public class TestActivity extends AppCompatActivity {

    private static final String TAG = "NATIVECALLHOOK";

    static {
        NativeCallHook.initialize();
        System.loadLibrary("liba");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        String mode = getIntent().getStringExtra("mode");
        if (mode == null) {
            Log.e(TAG, "TestActivity launched without mode extra");
            finish();
            return;
        }

        switch (mode) {
            case "benchmark":
                new Thread(this::runBenchmark).start();
                break;
            case "test_failsafe":
                runFailsafeTests();
                break;
            case "test_robustness":
                runRobustnessTests();
                break;
            case "test_overhead":
                runOverheadBenchmark();
                break;
            default:
                Log.e(TAG, "Unknown test mode: " + mode);
                finish();
        }
    }

    private void runFailsafeTests() {
        Log.i(TAG, "FAILSAFE_TEST: --- missing file ---");
        NativeCallHookTestHarness.testLoadFromPath("/data/local/tmp/nonexistent_library.so");

        Log.i(TAG, "FAILSAFE_TEST: --- empty file ---");
        String emptyPath = getCacheDir() + "/empty_test.so";
        try {
            new File(emptyPath).createNewFile();
            NativeCallHookTestHarness.testLoadFromPath(emptyPath);
            new File(emptyPath).delete();
        } catch (IOException e) {
            Log.e(TAG, "Failed to create empty test file: " + e.getMessage());
        }

        Log.i(TAG, "FAILSAFE_TEST: --- truncated file (2 bytes) ---");
        String truncPath = getCacheDir() + "/truncated_test.so";
        try (FileOutputStream fos = new FileOutputStream(truncPath)) {
            fos.write(new byte[]{0x16, 0x2c});
            fos.close();
            NativeCallHookTestHarness.testLoadFromPath(truncPath);
            new File(truncPath).delete();
        } catch (IOException e) {
            Log.e(TAG, "Failed to create truncated test file: " + e.getMessage());
        }

        Log.i(TAG, "FAILSAFE_TEST: complete");
    }

    private void runRobustnessTests() {
        Log.i(TAG, "ROBUSTNESS: starting");
        NativeCallHookTestHarness.testRepeatedLoad();
        NativeCallHookTestHarness.testConcurrentLoad(4);
        Log.i(TAG, "ROBUSTNESS: complete");
    }

    private void runBenchmark() {
        int[] sizes = {1024, 10240, 102400, 1048576, 5242880, 10485760};
        String[] labels = {"1KB", "10KB", "100KB", "1MB", "5MB", "10MB"};
        int iterations = 10;

        Log.i(TAG, "BENCHMARK: starting (" + sizes.length + " sizes, " + iterations + " iterations each)");

        for (int i = 0; i < sizes.length; i++) {
            String path = getCacheDir() + "/bench_" + labels[i] + ".enc";
            generateEncryptedTestFile(path, sizes[i]);
            NativeCallHookTestHarness.benchmarkDecryptPipeline(path, iterations);
            new File(path).delete();
        }

        Log.i(TAG, "BENCHMARK: complete");
    }

    private void runOverheadBenchmark() {
        Log.i(TAG, "OVERHEAD: starting");
        NativeCallHookTestHarness.benchmarkHookOverhead(1000);
        Log.i(TAG, "OVERHEAD: complete");
    }

    private void generateEncryptedTestFile(String path, int size) {
        try (FileOutputStream fos = new FileOutputStream(path)) {
            byte[] data = new byte[size];
            if (size >= 4) {
                data[0] = 0x16; data[1] = 0x2c; data[2] = 0x25; data[3] = 0x2f;
            }
            fos.write(data);
        } catch (IOException e) {
            Log.e(TAG, "Failed to generate benchmark file: " + e.getMessage());
        }
    }
}
