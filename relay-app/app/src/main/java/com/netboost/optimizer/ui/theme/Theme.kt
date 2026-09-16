package com.netboost.optimizer.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val ShieldColorScheme = lightColorScheme(
    primary = ShieldPrimary,
    onPrimary = ShieldSurface,
    primaryContainer = ShieldPrimaryDark,
    onPrimaryContainer = ShieldSurfaceContainerLow,
    secondary = ShieldSecondary,
    onSecondary = ShieldSurface,
    secondaryContainer = ShieldSecondaryContainer,
    onSecondaryContainer = ShieldOnSecondaryContainer,
    background = ShieldBackground,
    onBackground = ShieldTextPrimary,
    surface = ShieldSurface,
    onSurface = ShieldTextPrimary,
    surfaceVariant = ShieldSurfaceContainerHigh,
    onSurfaceVariant = ShieldTextSecondary,
    error = ShieldError,
    onError = ShieldSurface,
    errorContainer = ShieldErrorContainer,
    onErrorContainer = ShieldOnErrorContainer
)

@Composable
fun ShieldSMSTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = ShieldColorScheme,
        content = content
    )
}
