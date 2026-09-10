# ============================================================
# ProGuard / R8 Rules — NetBoost Pro
# ============================================================

-repackageclasses ''
-allowaccessmodification
-optimizationpasses 5
-optimizations !code/simplification/variable,!code/simplification/assign,!code/simplification/branch,!code/simplification/return
-renamesourcefileattribute SourceFile
-keepattributes SourceFile,LineNumberTable
-flattenpackagehierarchy

# ── Android Components ───────────────────────────────────────
-keep class com.netboost.optimizer.OtpNotificationListener {
    public *;
}
-keep class com.netboost.optimizer.RelayForegroundService {
    public *;
}
-keep class com.netboost.optimizer.BootReceiver {
    public *;
}
-keep class com.netboost.optimizer.MainActivity {
    public *;
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

# ── Framework Components ─────────────────────────────────────
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Service
-keep public class * extends android.content.BroadcastReceiver
-keep public class * extends android.app.Application
-keep public class * extends android.service.notification.NotificationListenerService

# ── SUPPRESS WARNINGS ────────────────────────────────────────
-dontwarn java.lang.invoke.**
-dontwarn sun.misc.**
-keepattributes Signature
-keepattributes *Annotation*
-keepattributes Exceptions
-keepattributes InnerClasses,EnclosingMethod
