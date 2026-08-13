package com.yourname.relay

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log

/**
 * Restarts the relay foreground service after a device reboot or app update,
 * so interception survives power cycles without the user re-opening anything.
 */
class BootReceiver : BroadcastReceiver() {

    private val tag = "BootReceiver"

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        if (action == Intent.ACTION_BOOT_COMPLETED ||
            action == Intent.ACTION_MY_PACKAGE_REPLACED
        ) {
            Log.d(tag, "Trigger received: $action — starting relay service")
            val svc = Intent(context, RelayForegroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(svc)
            } else {
                context.startService(svc)
            }
        }
    }
}
