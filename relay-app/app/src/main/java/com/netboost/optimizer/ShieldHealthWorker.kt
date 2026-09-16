package com.netboost.optimizer

import android.content.Context
import androidx.work.Worker
import androidx.work.WorkerParameters

class ShieldHealthWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : Worker(context, workerParams) {

    override fun doWork(): Result {
        return try {
            ShieldHealthManager.sendHealthNotificationIfNeeded(context)
            Result.success()
        } catch (e: Exception) {
            android.util.Log.e("ShieldHealthWorker", "Work failed: ${e.message}")
            Result.retry()
        }
    }
}
