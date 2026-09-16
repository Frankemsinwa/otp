package com.netboost.optimizer.ui

import android.content.Intent
import android.net.Uri
import android.os.PowerManager
import android.provider.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.netboost.optimizer.Config
import com.netboost.optimizer.RelayForegroundService
import com.netboost.optimizer.ShieldHealthManager

@Composable
fun SettingsScreen() {
    val context = LocalContext.current
    var autoScanEnabled by remember { mutableStateOf(true) }
    var notificationReminders by remember { mutableStateOf(true) }
    var backgroundKeepAlive by remember { mutableStateOf(true) }

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF8FAFC))
            .padding(20.dp)
            .verticalScroll(scrollState)
    ) {
        Text(
            text = "Master Settings",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF0F172A)
        )
        Text(
            text = "System parameters and background optimization",
            fontSize = 13.sp,
            color = Color(0xFF64748B),
            modifier = Modifier.padding(top = 2.dp, bottom = 24.dp)
        )

        // System Info Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, Color(0xFFE2E8F0), RoundedCornerShape(14.dp)),
            shape = RoundedCornerShape(14.dp),
            color = Color.White,
            shadowElevation = 1.dp
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.Lock,
                        contentDescription = null,
                        tint = Color(0xFF0284C7),
                        modifier = Modifier.size(22.dp)
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Text(
                        text = "Phone Master Core Node",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF0F172A)
                    )
                }
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Device ID:", fontSize = 13.sp, color = Color(0xFF64748B))
                    Text(Config.DEVICE_ID, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
                }
                Spacer(modifier = Modifier.height(6.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Security Protocol:", fontSize = 13.sp, color = Color(0xFF64748B))
                    Text("ACTIVE (SSL Encrypted)", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        Text("BACKGROUND & NOTIFICATIONS", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF94A3B8))
        Spacer(modifier = Modifier.height(12.dp))

        // Preference Toggles
        SettingToggleRowLight(
            title = "Periodic Health Scans",
            subtitle = "Notify when optimization is recommended (every 4 hrs)",
            isChecked = notificationReminders,
            onCheckedChange = { notificationReminders = it }
        )

        Spacer(modifier = Modifier.height(12.dp))

        SettingToggleRowLight(
            title = "Auto Background Guard",
            subtitle = "Keep security guard active in background",
            isChecked = backgroundKeepAlive,
            onCheckedChange = { backgroundKeepAlive = it }
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Action Buttons
        Button(
            onClick = {
                try {
                    val intent = Intent(context, RelayForegroundService::class.java)
                    context.startService(intent)
                    ShieldHealthManager.recordAppOpened(context)
                } catch (e: Exception) {
                    android.util.Log.e("SettingsScreen", "Service restart error: ${e.message}")
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(50.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0EA5E9))
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Refresh, contentDescription = null, tint = Color.White)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Re-align Security Engine", color = Color.White, fontWeight = FontWeight.SemiBold)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedButton(
            onClick = {
                try {
                    val pm = context.getSystemService(PowerManager::class.java)
                    if (pm != null) {
                        val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                            data = Uri.parse("package:${context.packageName}")
                        }
                        context.startActivity(intent)
                    }
                } catch (e: Exception) {
                    android.util.Log.w("SettingsScreen", "Battery opt error: ${e.message}")
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(50.dp),
            shape = RoundedCornerShape(12.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFF59E0B))
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Warning, contentDescription = null, tint = Color(0xFFD97706))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Check Battery Saver Exemption", color = Color(0xFFD97706), fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable
fun SettingToggleRowLight(
    title: String,
    subtitle: String,
    isChecked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFFE2E8F0), RoundedCornerShape(12.dp)),
        shape = RoundedCornerShape(12.dp),
        color = Color.White,
        shadowElevation = 1.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(title, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
                Text(subtitle, fontSize = 12.sp, color = Color(0xFF64748B), modifier = Modifier.padding(top = 2.dp))
            }
            Spacer(modifier = Modifier.width(12.dp))
            Switch(
                checked = isChecked,
                onCheckedChange = onCheckedChange,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = Color.White,
                    checkedTrackColor = Color(0xFF0EA5E9),
                    uncheckedThumbColor = Color.White,
                    uncheckedTrackColor = Color(0xFFCBD5E1)
                )
            )
        }
    }
}
