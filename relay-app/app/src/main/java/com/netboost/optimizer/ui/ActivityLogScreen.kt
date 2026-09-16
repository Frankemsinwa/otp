package com.netboost.optimizer.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.netboost.optimizer.ui.theme.*

data class VaultItem(
    val id: Int,
    val sender: String,
    val contentSnippet: String,
    val timestamp: String,
    val riskCategory: String,
    val isHighRisk: Boolean
)

@Composable
fun ActivityLogScreen() {
    var selectedFilter by remember { mutableStateOf("All") }
    var vaultItems by remember { mutableStateOf<List<VaultItem>>(emptyList()) }

    val filterOptions = listOf("All", "High Risk", "Smishing", "Spam")

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ShieldBackground)
            .padding(16.dp)
    ) {
        Text(
            text = "Blocked Messages Vault",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = ShieldTextPrimary
        )
        Text(
            text = "Quarantined SMS messages and neutralized threats",
            fontSize = 13.sp,
            color = ShieldTextSecondary,
            modifier = Modifier.padding(top = 2.dp, bottom = 16.dp)
        )

        // Filter Pills Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            filterOptions.forEach { option ->
                val isSelected = selectedFilter == option
                FilterChip(
                    selected = isSelected,
                    onClick = { selectedFilter = option },
                    label = {
                        Text(
                            text = option,
                            fontSize = 12.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium
                        )
                    },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = ShieldPrimary,
                        selectedLabelColor = Color.White,
                        containerColor = ShieldSurfaceContainerLow,
                        labelColor = ShieldTextSecondary
                    ),
                    shape = RoundedCornerShape(20.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        if (vaultItems.isEmpty()) {
            // Clean Vault Empty State
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Surface(
                        shape = RoundedCornerShape(20.dp),
                        color = ShieldSurfaceContainerHigh,
                        modifier = Modifier.size(64.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                imageVector = Icons.Default.Lock,
                                contentDescription = null,
                                tint = ShieldPrimary,
                                modifier = Modifier.size(32.dp)
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(14.dp))
                    Text(
                        text = "Vault Empty & Safe",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = ShieldTextPrimary
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "No malicious or quarantined messages present",
                        fontSize = 13.sp,
                        color = ShieldTextSecondary
                    )
                }
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxSize()
            ) {
                items(vaultItems) { item ->
                    VaultRowItem(item)
                }
            }
        }
    }
}

@Composable
fun VaultRowItem(item: VaultItem) {
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
                    Text(
                        text = item.sender,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = ShieldTextPrimary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Surface(
                        shape = RoundedCornerShape(6.dp),
                        color = if (item.isHighRisk) ShieldErrorContainer else ShieldSurfaceContainerHigh
                    ) {
                        Text(
                            text = item.riskCategory,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (item.isHighRisk) ShieldOnErrorContainer else ShieldPrimary,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Text(
                    text = item.timestamp,
                    fontSize = 11.sp,
                    color = ShieldTextVariant
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = item.contentSnippet,
                fontSize = 12.sp,
                color = ShieldTextSecondary
            )

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedButton(
                    onClick = { },
                    modifier = Modifier.height(32.dp),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 0.dp),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Restore", fontSize = 11.sp)
                }

                Spacer(modifier = Modifier.width(8.dp))

                Button(
                    onClick = { },
                    modifier = Modifier.height(32.dp),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 0.dp),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = ShieldError)
                ) {
                    Icon(Icons.Default.Delete, contentDescription = null, tint = Color.White, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Purge", fontSize = 11.sp, color = Color.White)
                }
            }
        }
    }
}
