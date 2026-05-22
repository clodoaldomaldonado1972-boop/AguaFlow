package br.com.vivereprudente.aguaflow

import android.media.AudioManager
import android.media.ToneGenerator
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class BeepPlugin : FlutterPlugin, MethodChannel.MethodCallHandler {
    private lateinit var channel: MethodChannel

    override fun onAttachedToEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel = MethodChannel(binding.binaryMessenger, "aguaflow/beep")
        channel.setMethodCallHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        if (call.method == "beep") {
            try {
                val toneGen = ToneGenerator(AudioManager.STREAM_NOTIFICATION, 90)
                toneGen.startTone(ToneGenerator.TONE_PROP_BEEP, 200)
                toneGen.release()
                result.success(null)
            } catch (e: Exception) {
                result.error("BEEP_ERROR", e.message, null)
            }
        } else {
            result.notImplemented()
        }
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel.setMethodCallHandler(null)
    }
}
