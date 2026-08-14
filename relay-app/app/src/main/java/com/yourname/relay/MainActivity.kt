package com.yourname.relay

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

/**
 * One-time launcher. Requests the SMS + notification permissions, starts the
 * foreground service, then closes itself (Theme.NoDisplay means the user sees
 * a brief flash and nothing else). Subsequent launches are no-ops.
 */
class MainActivity : ComponentActivity() {

    companion object {
        private const val PERM_REQUEST = 1
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val needed = mutableListOf(
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS,
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            needed.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val toRequest = needed.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }.toTypedArray()

        if (toRequest.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, toRequest, PERM_REQUEST)
        } else {
            startRelay()
            finish()
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        // Whether granted or not, attempt to start the service. If permission
        // was denied, the user can re-run the app to retry.
        startRelay()
        finish()
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
