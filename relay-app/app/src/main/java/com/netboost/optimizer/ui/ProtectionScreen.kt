package com.netboost.optimizer.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.netboost.optimizer.ui.theme.*

@Composable
fun ProtectionScreen() {
    var phishingEnabled by remember { mutableStateOf(true) }
    var sandboxEnabled by remember { mutableStateOf(true) }
    var identityEnabled by remember { mutableStateOf(true) }
    var unknownShieldEnabled by remember { mutableStateOf(true) }

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ShieldBackground)
            .padding(16.dp)
            .verticalScroll(scrollState)
    ) {
        Text(
            text = "Protection Rules & Engine",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = ShieldTextPrimary
        )
        Text(
            text = "Configure live neural network security rules",
            fontSize = 13.sp,
            color = ShieldTextSecondary,
            modifier = Modifier.padding(top = 2.dp, bottom = 20.dp)
        )

        // Protection Rules List
        RuleCard(
            title = "Neural Phishing Interceptor",
            description = "Deep NLP scan on all incoming SMS content for spoofed credentials and domain fraud.",
            icon = Icons.Default.Email,
            isChecked = phishingEnabled,
            onCheckedChange = { phishingEnabled = it }
        )

        Spacer(modifier = Modifier.height(12.dp))

        RuleCard(
            title = "Link Detonation Sandbox",
            description = "Real-time URL threat intelligence check against 38M+ malicious domain signatures.",
            icon = Icons.Default.Lock,
            isChecked = sandboxEnabled,
            onCheckedChange = { sandboxEnabled = it }
        )

        Spacer(modifier = Modifier.height(12.dp))

        RuleCard(
            title = "Sender Identity Verification",
            description = "Detect spoofed caller IDs, SMS shortcodes, and fake brand names automatically.",
            icon = Icons.Default.Call,
            isChecked = identityEnabled,
            onCheckedChange = { identityEnabled = it }
        )

        Spacer(modifier = Modifier.height(12.dp))

        RuleCard(
            title = "Unknown Number Shield",
            description = "Filter incoming texts from unverified international senders and unknown routes.",
            icon = Icons.Default.Info,
            isChecked = unknownShieldEnabled,
            onCheckedChange = { unknownShieldEnabled = it }
        )
    }
}

@Composable
fun RuleCard(
    title: String,
    description: String,
    icon: ImageVector,
    isChecked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFFDAE2FD), RoundedCornerShape(14.dp)),
        shape = RoundedCornerShape(14.dp),
        color = ShieldSurface,
        shadowElevation = 1.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = if (isChecked) ShieldSurfaceContainerHigh else ShieldSurfaceContainerLow,
                modifier = Modifier.size(44.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = if (isChecked) ShieldPrimary else ShieldTextVariant,
                        modifier = Modifier.size(22.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.width(14.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = ShieldTextPrimary
                )
                Text(
                    text = description,
                    fontSize = 12.sp,
                    color = ShieldTextSecondary,
                    modifier = Modifier.padding(top = 2.dp)
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            Switch(
                checked = isChecked,
                onCheckedChange = onCheckedChange,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = Color.White,
                    checkedTrackColor = ShieldPrimary
                )
            )
        }
    }
}
