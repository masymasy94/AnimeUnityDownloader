package com.hasasiero.tvstream

import android.app.Application
import android.util.Log
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class TvStreamApp : Application() {
    override fun onCreate() {
        super.onCreate()

        // Global crash handler — log the error for debugging
        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            Log.e("AnimeHub", "UNCAUGHT EXCEPTION", throwable)
            defaultHandler?.uncaughtException(thread, throwable)
        }
    }
}
