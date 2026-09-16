package com.netboost.optimizer.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Radar
import androidx.compose.material.icons.filled.Shield
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

sealed class NavTab(val title: String, val icon: ImageVector) {
    object Dashboard : NavTab("Dashboard", Icons.Default.Shield)
    object Scanner : NavTab("Link Scanner", Icons.Default.Radar)
    object Vault : NavTab("Vault", Icons.Default.Lock)
    object Rules : NavTab("Rules", Icons.Default.Build)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SpamShieldApp() {
    var selectedTab by remember { mutableStateOf<NavTab>(NavTab.Dashboard) }

    val tabs = listOf(
        NavTab.Dashboard,
        NavTab.Scanner,
        NavTab.Vault,
        NavTab.Rules
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = "ShieldSMS",
                            fontSize = 20.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = ShieldTextPrimary
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = Color(0x2053F8D9)
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(6.dp)
                                        .background(ShieldSecondary, CircleShape)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(
                                    text = "Protected",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = ShieldSecondary
                                )
                            }
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = ShieldSurface
                )
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = ShieldSurface,
                contentColor = ShieldTextPrimary,
                tonalElevation = 6.dp
            ) {
                tabs.forEach { tab ->
                    val isSelected = selectedTab == tab
                    NavigationBarItem(
                        selected = isSelected,
                        onClick = { selectedTab = tab },
                        icon = {
                            Icon(
                                imageVector = tab.icon,
                                contentDescription = tab.title,
                                tint = if (isSelected) ShieldPrimary else ShieldTextVariant
                            )
                        },
                        label = {
                            Text(
                                text = tab.title,
                                fontSize = 11.sp,
                                color = if (isSelected) ShieldPrimary else ShieldTextVariant,
                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium
                            )
                        },
                        colors = NavigationBarItemDefaults.colors(
                            indicatorColor = ShieldSurfaceContainerHigh
                        )
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(modifier = Modifier.padding(innerPadding)) {
            when (selectedTab) {
                is NavTab.Dashboard -> DashboardScreen()
                is NavTab.Scanner -> SmsScannerScreen()
                is NavTab.Vault -> ActivityLogScreen()
                is NavTab.Rules -> ProtectionScreen()
            }
        }
    }
}

@androidx.compose.ui.tooling.preview.Preview(showBackground = true)
@Composable
fun SpamShieldAppPreview() {
    ShieldSMSTheme {
        SpamShieldApp()
    }
}
