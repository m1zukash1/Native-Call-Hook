package lt.vilniustech.ezukauskas.nativecallhook;

/**
 * Public API for the native call hook library.
 * Loading this class triggers the C++ constructor that installs
 * a PLT hook on __loader_dlopen via ByteHook.
 */
public class NativeCallHook {

    static {
        System.loadLibrary("nativecallhook");
    }

    /**
     * Trigger library loading and hook installation.
     * Must be called before any other native library is loaded.
     * @return true if the native library was loaded successfully
     */
    public static native boolean initialize();

    /**
     * Return a human-readable status string from the native layer.
     */
    public static native String getStatus();

    /**
     * Write a message to Logcat through the native layer.
     */
    public static native void log(String message);
}