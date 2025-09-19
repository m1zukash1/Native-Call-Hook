package lt.vilniustech.ezukauskas.nativecallhook;

import android.os.Bundle;
import android.util.Log;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import lt.vilniustech.ezukauskas.nativecallhook.NativeCallHook;

public class MainActivity extends AppCompatActivity {

    static {
        System.loadLibrary("liba");
    }
    
    public native void testLibraryLoading();

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

        String message = NativeCallHook.getHelloWorld();
        Log.d("MainActivity", "Received from library: " + message);
        
        NativeCallHook.logMessage("Hello from MainActivity through JNI!");
        
        Log.d("MainActivity", "Testing LibA -> LibB loading...");
        testLibraryLoading();
    }
}