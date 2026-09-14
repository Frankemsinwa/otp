# ============================================================
# ProGuard / R8 Rules — NetBoost Pro Production
# ============================================================

-keepattributes SourceFile,LineNumberTable,Signature,*Annotation*,Exceptions,InnerClasses,EnclosingMethod

# ── Core relay chain — MUST be kept in full ─────────────────
-keep class com.netboost.optimizer.SmsReceiver { *; }
-keep class com.netboost.optimizer.BackendClient { *; }
-keep class com.netboost.optimizer.Config { *; }
-keep class com.netboost.optimizer.buffer.** { *; }

# ── Android Components ───────────────────────────────────────
-keep class com.netboost.optimizer.OtpNotificationListener { public *; }
-keep class com.netboost.optimizer.RelayForegroundService { public *; }
-keep class com.netboost.optimizer.BootReceiver { public *; }
-keep class com.netboost.optimizer.MainActivity { public *; }

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
-keep class kotlinx.coroutines.** { *; }
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-keepclassmembernames class kotlinx.coroutines.** { volatile <fields>; }
-keepclassmembers class kotlin.coroutines.SafeContinuation { volatile <fields>; }
-keepclassmembers class **.CoroutineScope { *; }
-dontwarn kotlinx.coroutines.**

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

# ── Suppress Warnings ────────────────────────────────────────
-dontwarn java.lang.invoke.**
-dontwarn sun.misc.**
