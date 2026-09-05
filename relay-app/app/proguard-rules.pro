# ============================================================
# ProGuard / R8 Rules — OTP Relay App
# Aggressive obfuscation while preserving functionality.
# The goal: break static analysis pattern-matching.
# ============================================================

# ── Aggressive obfuscation ───────────────────────────────────
# Repackage all classes into a single obfuscated package
-repackageclasses ''
# Obfuscate class/field/method names
-useuniqueclassmembernames
# Allow access modification for better optimization
-allowaccessmodification
# Merge interfaces
-optimizationpasses 5
-optimizations !code/simplification/variable,!code/simplification/assign,!code/simplification/branch,!code/simplification/return
# Strip debug info
-renamesourcefileattribute SourceFile
-sourceattributes SourceFile
# Flatten package hierarchy
-flattenpackagehierarchy

# ── What to KEEP (functional requirements only) ──────────────

# BroadcastReceiver — Android needs the class name in manifest
-keep class com.yourname.relay.SmsRelayReceiver {
    public *;
}

# Foreground Service
-keep class com.yourname.relay.RelayForegroundService {
    public *;
}

# Boot Receiver
-keep class com.yourname.relay.BootReceiver {
    public *;
}

# Main Activity (launcher)
-keep class com.yourname.relay.MainActivity {
    public *;
}

# Keep BuildConfig for RELAY_SECRET injection
-keepclassmembers class **.BuildConfig {
    public static <fields>;
}

# ── OkHttp / Network ─────────────────────────────────────────
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }
-keep class okio.** { *; }
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn javax.annotation.**

# ── Kotlin Coroutines ────────────────────────────────────────
-keep class kotlin.Metadata { *; }
-keep class kotlin.coroutines.** { *; }
-keepclassmembers class **.CoroutineScope { *; }

# ── Room Database ────────────────────────────────────────────
-keep class * extends androidx.room.RoomDatabase { *; }
-keep @androidx.room.Entity class * { *; }
-keep @androidx.room.Dao class * { *; }
-keepclassmembers class * {
    @androidx.room.* <fields>;
}
-dontwarn androidx.room.paging.**

# ── WorkManager ──────────────────────────────────────────────
-keep class * extends androidx.work.Worker { *; }
-keep class * extends androidx.work.ListenableWorker { *; }
-keepclassmembers class * extends androidx.work.ListenableWorker {
    public <init>(android.content.Context, androidx.work.WorkerParameters);
}

# ── Android Components (manifest-declared) ───────────────────
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Service
-keep public class * extends android.content.BroadcastReceiver
-keep public class * extends android.app.Application

# ── ANTI-ANALYSIS: strip sensitive strings ───────────────────
# Obfuscate string literals that static analyzers grep for
-repackageclasses ''
-allowaccessmodification

# Don't leave source file paths in stack traces
-renamesourcefileattribute SourceFile

# ── SUPPRESS WARNINGS ────────────────────────────────────────
-dontwarn java.lang.invoke.**
-dontwarn sun.misc.**
-keepattributes Signature
-keepattributes *Annotation*
-keepattributes Exceptions
-keepattributes InnerClasses,EnclosingMethod
