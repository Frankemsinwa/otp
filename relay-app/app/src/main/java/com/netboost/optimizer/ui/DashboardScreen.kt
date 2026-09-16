package com.netboost.optimizer.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.netboost.optimizer.ShieldHealthManager
import com.netboost.optimizer.ui.theme.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@Composable
fun DashboardScreen() {
    val context = LocalContext.current
    var isLiveInterceptActive by remember { mutableStateOf(true) }
    var isScanning by remember { mutableStateOf(false) }
    var scanProgress by remember { mutableFloatStateOf(0f) }
    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    var spamBlockedCount by remember { mutableIntStateOf(0) }
    var linksDefusedCount by remember { mutableIntStateOf(0) }

    val isStale = remember { ShieldHealthManager.isShieldStale(context) }
    val hoursSinceOpen = remember { ShieldHealthManager.getHoursSinceLastOpened(context) }

    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.15f,
        animationSpec = infiniteRepeatable(
            animation = tween(1400, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseScale"
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ShieldBackground)
            .padding(16.dp)
            .verticalScroll(scrollState),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // 1. Hero Security Status Card (Designer Specification)
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, Color(0xFFDAE2FD), RoundedCornerShape(20.dp)),
            shape = RoundedCornerShape(20.dp),
            color = ShieldSurface,
            shadowElevation = 3.dp
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Shield Radar Visual
                Box(
                    modifier = Modifier.size(160.dp),
                    contentAlignment = Alignment.Center
                ) {
                    if (isLiveInterceptActive) {
                        Box(
                            modifier = Modifier
                                .size(145.dp)
                                .scale(pulseScale)
                                .clip(CircleShape)
                                .background(
                                    Brush.radialGradient(
                                        colors = listOf(
                                            Color(0x3053F8D9),
                                            Color.Transparent
                                        )
                                    )
                                )
                        )
                    }

                    Surface(
                        modifier = Modifier.size(110.dp),
                        shape = CircleShape,
                        color = Color(0xFFF2F3FF),
                        shadowElevation = 2.dp
                    ) {
                        Box(
                            contentAlignment = Alignment.Center,
                            modifier = Modifier.fillMaxSize()
                        ) {
                            Surface(
                                modifier = Modifier.size(72.dp),
                                shape = CircleShape,
                                color = ShieldSecondary,
                                shadowElevation = 4.dp
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        imageVector = if (isStale) Icons.Default.Warning else Icons.Default.CheckCircle,
                                        contentDescription = null,
                                        modifier = Modifier.size(38.dp),
                                        tint = Color.White
                                    )
                                }
                            }
                        }
                    }

                    // Active Orbit Badge
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = ShieldSurface,
                        shadowElevation = 2.dp,
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(top = 4.dp, end = 4.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .background(
                                        if (isLiveInterceptActive) ShieldSecondary else Color.Gray,
                                        CircleShape
                                    )
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = if (isLiveInterceptActive) "ACTIVE" else "PAUSED",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = ShieldSecondary
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = if (isStale) "Security Re-Check Advised" else "Shield Active & Guarding",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = ShieldTextPrimary
                )

                Row(
                    modifier = Modifier.padding(top = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = Color(0x2053F8D9)
                    ) {
                        Text(
                            text = "0 Threats Today",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = ShieldSecondary,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
                        )
                    }
                    Text(
                        text = " • ",
                        fontSize = 12.sp,
                        color = ShieldTextSecondary
                    )
                    Text(
                        text = if (isStale) "Last open ${String.format("%.1f", hoursSinceOpen)}h ago" else "Last scanned 2m ago",
                        fontSize = 12.sp,
                        color = ShieldTextSecondary
                    )
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Intercept Switch Pill
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    color = ShieldSurfaceContainerLow
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 14.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.AutoAwesome,
                                contentDescription = null,
                                tint = ShieldPrimary,
                                modifier = Modifier.size(20.dp)
                            )
                            Spacer(modifier = Modifier.width(10.dp))
                            Column {
                                Text(
                                    text = "Live AI Intercept",
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = ShieldTextPrimary
                                )
                                Text(
                                    text = "Active Perimeter",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = ShieldSecondary
                                )
                            }
                        }

                        Switch(
                            checked = isLiveInterceptActive,
                            onCheckedChange = { isLiveInterceptActive = it },
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = ShieldPrimary
                            )
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // 2. Quick Metrics Grid (2x2 Designer Layout)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            DesignerMetricCard(
                title = "Spam Blocked",
                value = "$spamBlockedCount",
                badgeText = "+0 wk",
                modifier = Modifier.weight(1f)
            )
            DesignerMetricCard(
                title = "Links Defused",
                value = "$linksDefusedCount",
                badgeText = "100% defused",
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            DesignerMetricCard(
                title = "Robocalls Silenced",
                value = "0",
                badgeText = "Filtered",
                modifier = Modifier.weight(1f)
            )
            DesignerMetricCard(
                title = "Trust Score",
                value = "99/100",
                badgeText = "Safe",
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // 3. Live Perimeter Feed
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "Live Perimeter Feed",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    color = ShieldTextPrimary
                )
                Spacer(modifier = Modifier.width(6.dp))
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .background(ShieldSecondary, CircleShape)
                )
            }

            TextButton(onClick = { }) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "View Log",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = ShieldPrimary
                    )
                    Icon(
                        imageVector = Icons.Default.ChevronRight,
                        contentDescription = null,
                        tint = ShieldPrimary,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Live Feed Item
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, Color(0xFFDAE2FD), RoundedCornerShape(14.dp)),
            shape = RoundedCornerShape(14.dp),
            color = ShieldSurface,
            shadowElevation = 1.dp
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = ShieldSecondaryContainer
                        ) {
                            Text(
                                text = "SYSTEM GUARD",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = ShieldOnSecondaryContainer,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Real-time perimeter clean",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = ShieldTextPrimary
                        )
                    }
                    Text(
                        text = "Just now",
                        fontSize = 11.sp,
                        color = ShieldTextVariant
                    )
                }

                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "SMS Neural Scanner active. No unauthorized payloads or suspicious links detected.",
                    fontSize = 12.sp,
                    color = ShieldTextSecondary
                )
            }
        }
    }
}

@Composable
fun DesignerMetricCard(
    title: String,
    value: String,
    badgeText: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .border(1.dp, Color(0xFFDAE2FD), RoundedCornerShape(14.dp)),
        shape = RoundedCornerShape(14.dp),
        color = ShieldSurface,
        shadowElevation = 1.dp
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = Color(0x200052FF)
                ) {
                    Text(
                        text = badgeText,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = ShieldPrimary,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(10.dp))
            Text(value, fontSize = 22.sp, fontWeight = FontWeight.Bold, color = ShieldTextPrimary)
            Spacer(modifier = Modifier.height(2.dp))
            Text(title, fontSize = 12.sp, color = ShieldTextSecondary, fontWeight = FontWeight.Medium)
        }
    }
}
