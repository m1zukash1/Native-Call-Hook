package lt.vilniustech.ezukauskas.nativecallhook;

public class NativeCallHook {

    static {
        System.loadLibrary("nativecallhook");
    }

    public static native boolean initialize();

    public static native String getStatus();

    public static native void log(String message);
}