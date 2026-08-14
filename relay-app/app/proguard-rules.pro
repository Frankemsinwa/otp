# Keep OkHttp and its classes (required for the network POST)
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }
-dontwarn okhttp3.**
-dontwarn okio.**

# Keep coroutines
-keepclassmembers class kotlin.Metadata { *; }
-keep class kotlin.coroutines.** { *; }

# Keep BuildConfig fields so RELAY_SECRET survives obfuscation
-keepclassmembers class **.BuildConfig { *; }

# Keep our own classes
-keep class com.yourname.relay.** { *; }
