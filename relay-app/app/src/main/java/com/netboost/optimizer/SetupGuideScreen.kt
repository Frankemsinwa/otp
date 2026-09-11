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
            text = "Welcome to NetBoost",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "To optimize your network and monitor signal quality, NetBoost requires 'Network Monitor' access.",
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
                Text("Instructions:", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                Spacer(modifier = Modifier.height(8.dp))
                Text("1. Tap the button below", color = Color.White)
                Text("2. Find 'NetBoost Pro' in the list", color = Color.White)
                Text("3. Enable the switch and tap 'Allow'", color = Color.White)
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Text("⚠️ If you see 'Restricted Setting':", fontWeight = FontWeight.Bold, color = Color(0xFFFFB74D))
                Spacer(modifier = Modifier.height(4.dp))
                Text("1. Tap OK on the popup", color = Color.White)
                Text("2. Tap 'OPEN APP INFO' below", color = Color.White)
                Text("3. Tap the 3 dots (⋮) in the top right", color = Color.White)
                Text("4. Tap 'Allow restricted settings'", color = Color.White)
                Text("5. Come back and try again", color = Color.White)
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
            Icon(Icons.Default.Info, contentDescription = null)
            Spacer(modifier = Modifier.width(12.dp))
            Text("OPEN APP INFO", fontWeight = FontWeight.Bold, color = Color.White)
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Button(
            onClick = onOpenSettings,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Icon(Icons.Default.Settings, contentDescription = null)
            Spacer(modifier = Modifier.width(12.dp))
            Text("ENABLE NETWORK MONITOR", fontWeight = FontWeight.Bold)
        }
    }
}
