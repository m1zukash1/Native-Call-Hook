package lt.vilniustech.ezukauskas.nativecallhook;

import android.os.Bundle;
import android.util.Log;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/**
 * Demo activity that exercises the native call hook library.
 * Initializes the hook, loads a native library that in turn loads
 * an encrypted library, demonstrating the full interception flow.
 */
public class MainActivity extends AppCompatActivity {

    private static final String TAG = "NATIVECALLHOOK";

    static {
        // Initialize the dlopen hook FIRST — before loading any other native libraries.
        // This ensures all subsequent dlopen calls pass through the hook.
        NativeCallHook.initialize();

        // Load the demo library; its dlopen("liblibb.so") call will be intercepted.
        System.loadLibrary("liba");
    }

    public native void loadEncryptedLibrary();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        Log.i(TAG, NativeCallHook.getStatus());
        NativeCallHook.log("MainActivity started");

        // Trigger the liba → liblibb loading chain (liblibb.so is encrypted on disk)
        loadEncryptedLibrary();
    }
}