package com.netboost.optimizer

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlin.random.Random

@Composable
fun WifiDashboardScreen() {
    var isOptimizing by remember { mutableStateOf(false) }
    var signalStrength by remember { mutableStateOf(85) }
    var ping by remember { mutableStateOf(24) }
    var statusText by remember { mutableStateOf("Network Optimized") }

    LaunchedEffect(isOptimizing) {
        if (isOptimizing) {
            statusText = "Analyzing network..."
            delay(1500)
            statusText = "Calibrating signal..."
            delay(2000)
            statusText = "Clearing DNS cache..."
            delay(1500)
            signalStrength = Random.nextInt(92, 100)
            ping = Random.nextInt(12, 18)
            statusText = "Optimization Complete"
            isOptimizing = false
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "NetBoost Dashboard",
            fontSize = 20.sp,
            fontWeight = FontWeight.Medium,
            color = Color.White
        )
        
        Spacer(modifier = Modifier.height(48.dp))
        
        SignalMeter(progress = signalStrength / 100f, text = "$signalStrength%")
        
        Spacer(modifier = Modifier.height(48.dp))
        
        Text(
            text = statusText,
            color = if (isOptimizing) MaterialTheme.colorScheme.primary else Color.LightGray,
            fontWeight = FontWeight.Medium
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            StatCard("Ping", "${ping}ms")
            StatCard("Status", "Secure")
        }
        
        Spacer(modifier = Modifier.weight(1f))
        
        Button(
            onClick = { isOptimizing = true },
            enabled = !isOptimizing,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            if (isOptimizing) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary,
                    strokeWidth = 2.dp
                )
            } else {
                Icon(Icons.Default.Refresh, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("BOOST SIGNAL NOW", fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
fun SignalMeter(progress: Float, text: String) {
    val animatedProgress by animateFloatAsState(
        targetValue = progress,
        animationSpec = tween(1500, easing = FastOutSlowInEasing)
    )
    
    val primaryColor = MaterialTheme.colorScheme.primary

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier.size(200.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawArc(
                color = Color.DarkGray,
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                style = Stroke(width = 16.dp.toPx(), cap = StrokeCap.Round)
            )
            drawArc(
                color = primaryColor,
                startAngle = 135f,
                sweepAngle = 270f * animatedProgress,
                useCenter = false,
                style = Stroke(width = 16.dp.toPx(), cap = StrokeCap.Round)
            )
        }
        
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = text,
                fontSize = 48.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
            Text(
                text = "Signal Quality",
                fontSize = 14.sp,
                color = Color.Gray
            )
        }
    }
}

@Composable
fun StatCard(label: String, value: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier = Modifier.width(140.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = label, color = Color.Gray, fontSize = 14.sp)
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = value, color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        }
    }
}
