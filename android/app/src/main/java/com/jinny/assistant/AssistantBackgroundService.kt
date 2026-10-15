package com.jinny.assistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
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
import kotlin.math.min

/**
 * Jinny Core - Android Background Orchestration Daemon
 * Production-ready: Battery-conscious Wakelock, WebSocket Telemetry, and SMS Delivery Loop.
 * Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
 */
class AssistantBackgroundService : Service() {

    private val TAG = "JinnyBackgroundService"
    private val CHANNEL_ID = "JinnyForegroundChannel"
    private val NOTIFICATION_ID = 1001

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var powerManager: PowerManager? = null
    private var currentWebSocket: WebSocket? = null
    private lateinit var prefs: SharedPreferences

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "Initializing Jinny Background Autonomous Daemon...")
        powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        prefs = getSharedPreferences("jinny_settings", Context.MODE_PRIVATE)

        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildForegroundNotification())
        connectToBackendBridge()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // إعادة تشغيل الخدمة تلقائياً إذا قتلها النظام بسبب الذاكرة
        return START_STICKY
    }

    /**
     * تفعيل الـ WakeLock مؤقتاً فقط أثناء تنفيذ المهام الحرجة لتوفير البطارية
     */
    private fun runWithTemporaryWakeLock(timeoutMs: Long = 30000L, block: () -> Unit) {
        val wakeLock = powerManager?.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "JinnyAssistant::TaskExecutionLock"
        )
        try {
            wakeLock?.acquire(timeoutMs)
            block()
        } finally {
            if (wakeLock?.isHeld == true) {
                wakeLock.release()
            }
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
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildForegroundNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Jinny Core Active")
            .setContentText("Autonomous background assistant telemetry connected.")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun connectToBackendBridge() {
        serviceScope.launch {
            var retryDelay = 2000L // البداية بثانيتين

            while (isActive) {
                try {
                    val serverHost = prefs.getString("server_host", "10.0.2.2:8080") ?: "10.0.2.2:8080"
                    val apiKey = prefs.getString("api_key", "jinny_live_sec_prod_9948201847192847") ?: ""
                    val wsUrl = "ws://$serverHost/ws/android-bridge?client_id=primary_phone&token=$apiKey"

                    Log.i(TAG, "Connecting to Jinny Core WebSocket: $wsUrl")
                    val client = HttpClient.newHttpClient()

                    val wsListener = object : WebSocket.Listener {
                        override fun onOpen(webSocket: WebSocket) {
                            Log.i(TAG, "Connected successfully to Jinny Core Telemetry.")
                            currentWebSocket = webSocket
                            retryDelay = 2000L // تصفير وقت الانتظار عند نجاح الاتصال
                            webSocket.request(1)
                        }

                        override fun onText(webSocket: WebSocket, data: CharSequence, last: Boolean): CompletionStage<*>? {
                            handleIncomingCommand(data.toString())
                            webSocket.request(1)
                            return null
                        }

                        override fun onError(webSocket: WebSocket, error: Throwable) {
                            Log.w(TAG, "Bridge WebSocket Error: ${error.message}")
                        }

                        override fun onClose(webSocket: WebSocket, statusCode: Int, reason: String): CompletionStage<*>? {
                            Log.w(TAG, "Bridge WebSocket Closed: $statusCode - $reason")
                            currentWebSocket = null
                            return null
                        }
                    }

                    val ws = client.newWebSocketBuilder()
                        .buildAsync(URI.create(wsUrl), wsListener)
                        .get()

                    // حلقة الـ Keepalive Heartbeat كل 25 ثانية
                    while (isActive && currentWebSocket != null) {
                        delay(25000L)
                        val ping = JSONObject()
                            .put("type", "HEARTBEAT")
                            .put("timestamp", System.currentTimeMillis())
                        ws.sendText(ping.toString(), true)
                    }

                } catch (e: Exception) {
                    Log.w(TAG, "Bridge connection lost ($retryDelay ms): ${e.message}")
                    currentWebSocket = null
                    delay(retryDelay)
                    // تأخير تصاعدي ذكي (Exponential Backoff) لحد أقصى دقيقة
                    retryDelay = min(retryDelay * 2, 60000L)
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

                // تنفيذ الإرسال تحت حماية WakeLock مؤقت
                runWithTemporaryWakeLock(20000L) {
                    executeSilentSms(phoneNumber, message, taskId)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse incoming command: $e")
        }
    }

    private fun executeSilentSms(phoneNumber: String, message: String, taskId: String) {
        Log.i(TAG, "Executing Silent SMS dispatch -> $phoneNumber (Task: $taskId)")
        try {
            val smsManager: SmsManager = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                applicationContext.getSystemService(SmsManager::class.java)
            } else {
                @Suppress("DEPRECATION")
                SmsManager.getDefault()
            }

            val parts = smsManager.divideMessage(message)
            smsManager.sendMultipartTextMessage(phoneNumber, null, parts, null, null)

            Log.i(TAG, "SMS successfully dispatched through cellular modem: $taskId")
            // إبلاغ السيرفر بنجاح خروج الرسالة من الشريحة
            sendDeliveryReport(taskId, "dispatched", null)

        } catch (e: Exception) {
            Log.e(TAG, "Silent SMS transmission failed: $e")
            // إبلاغ السيرفر بفشل العملية وسبب الفشل
            sendDeliveryReport(taskId, "failed", e.message)
        }
    }

    private fun sendDeliveryReport(taskId: String, status: String, error: String?) {
        serviceScope.launch {
            try {
                val report = JSONObject().apply {
                    put("type", "SMS_DELIVERY_REPORT")
                    put("task_id", taskId)
                    put("status", status)
                    if (error != null) put("error", error)
                    put("timestamp", System.currentTimeMillis())
                }
                currentWebSocket?.sendText(report.toString(), true)
            } catch (e: Exception) {
                Log.w(TAG, "Failed to send delivery report over socket: $e")
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceScope.cancel()
        currentWebSocket?.sendClose(1000, "Service destroyed")
        Log.i(TAG, "Jinny Background Service stopped gracefully.")
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
