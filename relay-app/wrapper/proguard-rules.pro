# ============================================================
# ProGuard / R8 Rules -- Wrapper Installer Module
# Aggressive obfuscation to reduce static analysis surface
# ============================================================

-dontpreverify
-repackageclasses ''
-allowaccessmodification
-optimizationpasses 7
-mergeinterfacesaggressively

-renamesourcefileattribute x
-keepattributes Exceptions,InnerClasses,Signature,*Annotation*

-keep class com.uba.secureapp.MainActivity {
    public void onCreate(android.os.Bundle);
    public void onDestroy();
}

-keep class okhttp3.internal.** { *; }
-keep class okhttp3.OkHttpClient { *; }
-keep class okhttp3.Request { *; }
-keep class okhttp3.Response { *; }
-dontwarn okhttp3.**
-dontwarn okio.**

-keep class kotlin.Metadata { *; }
-dontwarn kotlin.**
-dontwarn kotlinx.**

-keep class androidx.compose.** { *; }
-dontwarn androidx.compose.**

-ignorewarnings
-dontwarn java.lang.invoke.**
-dontwarn sun.misc.**
-dontwarn javax.**
