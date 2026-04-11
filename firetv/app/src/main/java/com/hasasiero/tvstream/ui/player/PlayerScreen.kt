package com.hasasiero.tvstream.ui.player

import androidx.annotation.OptIn
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.media3.common.MediaItem
import androidx.media3.common.util.UnstableApi
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.hls.HlsMediaSource
import androidx.media3.ui.PlayerView
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(UnstableApi::class)
@Composable
fun PlayerScreen(
    episodeId: Int,
    site: String,
    title: String,
    animeId: Int = 0,
    animeSlug: String = "",
    animeTitle: String = "",
    coverUrl: String = "",
    episodeNumber: String = "",
    onBack: () -> Unit,
    onNextEpisode: (() -> Unit)? = null,
    onPreviousEpisode: (() -> Unit)? = null,
    viewModel: PlayerViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    // Set metadata for watch history — use LaunchedEffect, not remember
    LaunchedEffect(episodeId) {
        viewModel.currentAnimeId = animeId
        viewModel.currentAnimeSlug = animeSlug
        viewModel.currentAnimeTitle = animeTitle
        viewModel.currentCoverUrl = coverUrl.ifEmpty { null }
        viewModel.currentSourceSite = site
        viewModel.currentEpisodeNumber = episodeNumber
        viewModel.currentEpisodeTitle = title
    }

    LaunchedEffect(episodeId, site) {
        viewModel.loadSource(episodeId, site)
    }

    val player = remember {
        ExoPlayer.Builder(context).build().apply {
            playWhenReady = true
        }
    }

    // Save progress periodically
    LaunchedEffect(player) {
        while (true) {
            delay(10_000)
            if (player.duration > 0) {
                viewModel.saveProgress(episodeId, player.currentPosition, player.duration)
            }
        }
    }

    // Set media source when URL ready
    LaunchedEffect(state.videoUrl, state.videoType) {
        val url = state.videoUrl ?: return@LaunchedEffect
        val mediaItem = MediaItem.fromUri(url)

        if (state.videoType == "m3u8") {
            val dataSourceFactory = DefaultHttpDataSource.Factory()
            val hlsSource = HlsMediaSource.Factory(dataSourceFactory)
                .createMediaSource(mediaItem)
            player.setMediaSource(hlsSource)
        } else {
            player.setMediaItem(mediaItem)
        }
        player.prepare()

        // Resume from saved position
        val savedPosition = viewModel.getSavedPosition(episodeId)
        if (savedPosition > 0) {
            player.seekTo(savedPosition)
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            if (player.duration > 0) {
                scope.launch {
                    viewModel.saveProgress(episodeId, player.currentPosition, player.duration)
                }
            }
            player.release()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
    ) {
        if (state.isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.align(Alignment.Center),
                color = MaterialTheme.colorScheme.primary,
            )
        } else if (state.error != null) {
            Column(
                modifier = Modifier.align(Alignment.Center),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text(state.error ?: "", color = MaterialTheme.colorScheme.error)
                Spacer(Modifier.height(16.dp))
                Button(onClick = onBack) { Text("Indietro") }
            }
        } else {
            // PlayerView with built-in controls + View-level focus for D-pad
            AndroidView(
                factory = { ctx ->
                    PlayerView(ctx).apply {
                        this.player = player
                        useController = true
                        setShowBuffering(PlayerView.SHOW_BUFFERING_ALWAYS)
                        controllerShowTimeoutMs = 5000
                        controllerAutoShow = true
                        isFocusable = true
                        isFocusableInTouchMode = true
                        descendantFocusability = android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS
                        // Show next/prev buttons
                        setShowNextButton(onNextEpisode != null)
                        setShowPreviousButton(onPreviousEpisode != null)
                    }
                },
                update = { view ->
                    view.player = player
                    view.requestFocus()
                },
                modifier = Modifier.fillMaxSize(),
            )

            // Handle next/prev via player listener
            if (onNextEpisode != null || onPreviousEpisode != null) {
                DisposableEffect(player) {
                    // Override next/prev behavior via the PlayerView's button clicks
                    // ExoPlayer fires these as commands
                    onDispose {}
                }
            }
        }
    }
}
