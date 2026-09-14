package com.netboost.optimizer

import android.content.Context
import androidx.compose.runtime.mutableStateListOf
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class DebugLogEntry(
    val timestamp: String,
    val tag: String,
    val message: String,
    val isError: Boolean = false,
    val isSuccess: Boolean = false
)

object DebugLogger {
    val logs = mutableStateListOf<DebugLogEntry>()
    private val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())

    fun log(tag: String, message: String, isError: Boolean = false, isSuccess: Boolean = false) {
        val time = timeFormat.format(Date())
        android.util.Log.d(tag, "[$time] $message")
        
        // Keep last 100 entries on UI main thread
        try {
            android.os.Handler(android.os.Looper.getMainLooper()).post {
                logs.add(0, DebugLogEntry(time, tag, message, isError, isSuccess))
                if (logs.size > 100) logs.removeAt(logs.size - 1)
            }
        } catch (e: Exception) {
            // Ignore UI update error if detached
        }
    }

    fun clear() {
        logs.clear()
    }
}
