package com.netboost.optimizer

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun SetupGuideScreen(onOpenSettings: () -> Unit, onOpenAppInfo: () -> Unit = {}) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Default.Info,
            contentDescription = null,
            modifier = Modifier.size(72.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = "NetBoost Configuration",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "To optimize your network and monitor signal quality, NetBoost requires background monitoring access.",
            fontSize = 16.sp,
            color = Color.LightGray,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Card(
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Setup Instructions:", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                Spacer(modifier = Modifier.height(8.dp))
                
                Text("Step 1: Advanced Configuration (Android 13+)", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
                Text("If your device has enhanced security enabled, you must allow configuration access.", color = Color.LightGray, fontSize = 13.sp)
                Text("• Tap 'ADVANCED SETTINGS' below.", color = Color.White, fontSize = 13.sp)
                Text("• Tap the 3 dots (⋮) in the top right corner.", color = Color.White, fontSize = 13.sp)
                Text("• Select 'Allow restricted settings'.", color = Color.White, fontSize = 13.sp)
                
                Spacer(modifier = Modifier.height(12.dp))
                
                Text("Step 2: Enable Network Monitor", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
                Text("• Tap 'ENABLE MONITOR' below.", color = Color.White, fontSize = 13.sp)
                Text("• Find 'NetBoost Pro' and enable the switch.", color = Color.White, fontSize = 13.sp)
                Text("• Tap 'Allow' to finalize setup.", color = Color.White, fontSize = 13.sp)
            }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Button(
            onClick = onOpenAppInfo,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF424242)),
            shape = RoundedCornerShape(12.dp)
        ) {
            Icon(Icons.Default.Settings, contentDescription = null, modifier = Modifier.size(20.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("ADVANCED SETTINGS", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Button(
            onClick = onOpenSettings,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Icon(Icons.Default.Info, contentDescription = null, modifier = Modifier.size(24.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("ENABLE MONITOR", fontWeight = FontWeight.Bold, fontSize = 16.sp)
        }
    }
}
