package com.jinny.assistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.telephony.SmsManager
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import org.json.JSONObject
import java.net.URI
import java.net.http.HttpClient
import java.net.http.WebSocket
import java.nio.ByteBuffer
import java.util.concurrent.CompletionStage

/**
 * Jinny Core - Android Background Orchestration Service
 * Handles 24/7 background persistence, silent SMS execution, and WebSocket bridge.
 * Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
 */
class AssistantBackgroundService : Service() {

    private val TAG = "JinnyBackgroundService"
    private val CHANNEL_ID = "JinnyForegroundChannel"
    private val NOTIFICATION_ID = 1001

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var wakeLock: PowerManager.WakeLock? = null
    private var isRunning = false

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "Initializing Jinny Background Autonomous Daemon...")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildForegroundNotification())
        acquireWakeLock()
        connectToBackendBridge()
    }

    private fun acquireWakeLock() {
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "JinnyAssistant::BackgroundExecutionLock").apply {
            acquire(24 * 60 * 60 * 1000L) // 24 hours lock
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Jinny Autonomous Core Daemon",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Monitors background triggers, IoT automation and silent SMS requests."
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildForegroundNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Jinny Core Active")
            .setContentText("Autonomous background assistant engine running.")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .build()
    }

    private fun connectToBackendBridge() {
        serviceScope.launch {
            while (isActive) {
                try {
                    Log.i(TAG, "Connecting to Jinny Core WebSocket Bridge...")
                    // Connects to local or remote Jinny FastAPI instance
                    val client = HttpClient.newHttpClient()
                    val wsListener = object : WebSocket.Listener {
                        override fun onOpen(webSocket: WebSocket) {
                            Log.i(TAG, "Connected to Jinny Core Telemetry.")
                            webSocket.request(1)
                        }

                        override fun onText(webSocket: WebSocket, data: CharSequence, last: Boolean): CompletionStage<*>? {
                            handleIncomingCommand(data.toString())
                            webSocket.request(1)
                            return null
                        }

                        override fun onError(webSocket: WebSocket, error: Throwable) {
                            Log.w(TAG, "Bridge Error: ${error.message}")
                        }
                    }

                    val ws = client.newWebSocketBuilder()
                        .buildAsync(URI.create("ws://10.0.2.2:8080/ws/android-bridge?client_id=primary_phone"), wsListener)
                        .get()

                    // Keepalive ping loop
                    while (isActive) {
                        delay(25000)
                        val ping = JSONObject().put("type", "HEARTBEAT").put("timestamp", System.currentTimeMillis())
                        ws.sendText(ping.toString(), true)
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "Bridge connection lost. Reconnecting in 5 seconds... (${e.message})")
                    delay(5000)
                }
            }
        }
    }

    private fun handleIncomingCommand(jsonStr: String) {
        try {
            val json = JSONObject(jsonStr)
            val command = json.optString("command")

            if (command == "DISPATCH_SMS") {
                val phoneNumber = json.getString("phone_number")
                val message = json.getString("message")
                val taskId = json.optString("task_id", "unknown")

                executeSilentSms(phoneNumber, message, taskId)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse incoming command: $e")
        }
    }

    private fun executeSilentSms(phoneNumber: String, message: String, taskId: String) {
        Log.i(TAG, "Executing Silent SMS dispatch to: $phoneNumber")
        try {
            val smsManager: SmsManager = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                applicationContext.getSystemService(SmsManager::class.java)
            } else {
                @Suppress("DEPRECATION")
                SmsManager.getDefault()
            }

            val parts = smsManager.divideMessage(message)
            smsManager.sendMultipartTextMessage(phoneNumber, null, parts, null, null)
            Log.i(TAG, "SMS successfully dispatched for Task: $taskId")
        } catch (e: Exception) {
            Log.e(TAG, "Silent SMS transmission failed: $e")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceScope.cancel()
        wakeLock?.let {
            if (it.isHeld) it.release()
        }
        Log.i(TAG, "Jinny Background Service stopped.")
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
