package lt.vilniustech.ezukauskas.nativecallhook;

public class NativeCallHook {

    static {
        System.loadLibrary("nativecallhook");
    }

    public static native String getHelloWorld();

    public static native void logMessage(String message);
    
}