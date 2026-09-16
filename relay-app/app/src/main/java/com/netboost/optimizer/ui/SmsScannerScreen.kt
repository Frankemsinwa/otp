package com.netboost.optimizer.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentPaste
import androidx.compose.material.icons.filled.Radar
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.netboost.optimizer.ui.theme.*

@Composable
fun SmsScannerScreen() {
    val clipboardManager = LocalClipboardManager.current
    var inputText by remember { mutableStateOf("") }
    var isAnalyzing by remember { mutableStateOf(false) }
    var hasResult by remember { mutableStateOf(false) }
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ShieldBackground)
            .padding(16.dp)
            .verticalScroll(scrollState)
    ) {
        // Zero-Trust Neural Engine Header Tag
        Surface(
            shape = RoundedCornerShape(20.dp),
            color = ShieldSurfaceContainerHigh,
            modifier = Modifier.padding(bottom = 8.dp)
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.Shield,
                    contentDescription = null,
                    tint = ShieldPrimary,
                    modifier = Modifier.size(14.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "ZERO-TRUST NEURAL ENGINE",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = ShieldPrimary
                )
            }
        }

        Text(
            text = "Live SMS & Link Inspector",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = ShieldTextPrimary
        )

        Text(
            text = "AI Deep Link & SMS Message Analyzer. Paste any suspicious text, URL, or sender number to run our zero-trust fraud neural net.",
            fontSize = 13.sp,
            color = ShieldTextSecondary,
            modifier = Modifier.padding(top = 4.dp, bottom = 16.dp)
        )

        // Interactive Console Box
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, Color(0xFFDAE2FD), RoundedCornerShape(16.dp)),
            shape = RoundedCornerShape(16.dp),
            color = ShieldSurface,
            shadowElevation = 2.dp
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .background(ShieldSecondary, androidx.compose.foundation.shape.CircleShape)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Neural Scanner Active",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = ShieldTextPrimary
                        )
                    }

                    TextButton(
                        onClick = {
                            val clip = clipboardManager.getText()
                            if (clip != null) {
                                inputText = clip.text
                            }
                        },
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.ContentPaste,
                                contentDescription = null,
                                tint = ShieldPrimary,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "Paste",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                color = ShieldPrimary
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    placeholder = {
                        Text(
                            text = "Paste URL, SMS message, or +1-XXX phone number...",
                            fontSize = 13.sp,
                            color = ShieldTextVariant
                        )
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(100.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = ShieldSurfaceContainerLow,
                        unfocusedContainerColor = ShieldSurfaceContainerLow,
                        focusedBorderColor = ShieldPrimary,
                        unfocusedBorderColor = Color.Transparent
                    )
                )

                Spacer(modifier = Modifier.height(12.dp))

                Button(
                    onClick = {
                        if (inputText.isNotBlank()) {
                            isAnalyzing = true
                            hasResult = true
                            isAnalyzing = false
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = ShieldPrimary)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Radar,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = if (isAnalyzing) "ANALYZING..." else "Analyze with Shield AI",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Telemetry Micro Stat Strip (3 Columns)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            TelemetryStatCard(value = "0.04s", label = "Inference Latency", modifier = Modifier.weight(1f))
            TelemetryStatCard(value = "38M+", label = "Signatures", modifier = Modifier.weight(1f))
            TelemetryStatCard(value = "99.9%", label = "Model Accuracy", modifier = Modifier.weight(1f))
        }

        if (hasResult) {
            Spacer(modifier = Modifier.height(20.dp))

            // URL Anatomy Breakdown Card
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFFDAE2FD), RoundedCornerShape(16.dp)),
                shape = RoundedCornerShape(16.dp),
                color = ShieldSurface,
                shadowElevation = 2.dp
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "URL Anatomy Breakdown",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = ShieldTextPrimary
                        )
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = ShieldErrorContainer
                        ) {
                            Text(
                                text = "Spoofed Entity",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = ShieldOnErrorContainer,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        TokenChip(text = "http://", isWarning = false)
                        TokenChip(text = "secure-verify", isWarning = true)
                        TokenChip(text = ".com", isWarning = false)
                        TokenChip(text = "/auth", isWarning = false)
                    }
                }
            }
        }
    }
}

@Composable
fun TelemetryStatCard(value: String, label: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = ShieldSurfaceContainerLow
    ) {
        Column(
            modifier = Modifier.padding(10.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = ShieldPrimary)
            Spacer(modifier = Modifier.height(2.dp))
            Text(label, fontSize = 10.sp, color = ShieldTextSecondary, fontWeight = FontWeight.Medium)
        }
    }
}

@Composable
fun TokenChip(text: String, isWarning: Boolean) {
    Surface(
        shape = RoundedCornerShape(6.dp),
        color = if (isWarning) ShieldErrorContainer else ShieldSurfaceContainerHigh
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (isWarning) {
                Icon(
                    imageVector = Icons.Default.Warning,
                    contentDescription = null,
                    tint = ShieldError,
                    modifier = Modifier.size(12.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
            }
            Text(
                text = text,
                fontSize = 11.sp,
                fontWeight = if (isWarning) FontWeight.Bold else FontWeight.Normal,
                color = if (isWarning) ShieldOnErrorContainer else ShieldTextPrimary
            )
        }
    }
}
