package com.hasasiero.tvstream.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.toRoute
import com.hasasiero.tvstream.ui.detail.DetailScreen
import com.hasasiero.tvstream.ui.home.HomeScreen
import com.hasasiero.tvstream.ui.player.PlayerScreen
import com.hasasiero.tvstream.ui.settings.SettingsScreen
import kotlinx.serialization.Serializable

@Serializable
object Home

@Serializable
data class Detail(val animeId: Int, val slug: String, val site: String)

@Serializable
data class Player(
    val episodeId: Int,
    val site: String,
    val title: String,
    val animeId: Int,
    val animeSlug: String,
    val animeTitle: String,
    val coverUrl: String = "",
    val episodeNumber: String = "",
    // Next episode info (empty = no next)
    val nextEpisodeId: Int = -1,
    val nextEpisodeNumber: String = "",
    val prevEpisodeId: Int = -1,
    val prevEpisodeNumber: String = "",
)

@Serializable
object Settings

@Composable
fun AppNavGraph() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = Home) {
        composable<Home> {
            HomeScreen(
                onAnimeClick = { anime ->
                    navController.navigate(Detail(anime.id, anime.slug, anime.sourceSite))
                },
                onContinueWatching = { entry ->
                    navController.navigate(
                        Player(
                            episodeId = entry.episodeId,
                            site = entry.sourceSite,
                            title = "${entry.animeTitle} - EP ${entry.episodeNumber}",
                            animeId = entry.animeId,
                            animeSlug = entry.animeSlug,
                            animeTitle = entry.animeTitle,
                            coverUrl = entry.coverUrl ?: "",
                            episodeNumber = entry.episodeNumber,
                        )
                    )
                },
                onSettingsClick = { navController.navigate(Settings) },
            )
        }

        composable<Detail> { backStackEntry ->
            val route = backStackEntry.toRoute<Detail>()
            DetailScreen(
                animeId = route.animeId,
                slug = route.slug,
                site = route.site,
                onPlayEpisode = { episodeId, epNumber, epTitle, coverUrl, nextId, nextNum, prevId, prevNum ->
                    navController.navigate(
                        Player(
                            episodeId = episodeId,
                            site = route.site,
                            title = epTitle,
                            animeId = route.animeId,
                            animeSlug = route.slug,
                            animeTitle = route.slug, // will be overridden
                            coverUrl = coverUrl ?: "",
                            episodeNumber = epNumber,
                            nextEpisodeId = nextId,
                            nextEpisodeNumber = nextNum,
                            prevEpisodeId = prevId,
                            prevEpisodeNumber = prevNum,
                        )
                    )
                },
                onBack = { navController.popBackStack() },
            )
        }

        composable<Player> { backStackEntry ->
            val route = backStackEntry.toRoute<Player>()
            PlayerScreen(
                episodeId = route.episodeId,
                site = route.site,
                title = route.title,
                animeId = route.animeId,
                animeSlug = route.animeSlug,
                animeTitle = route.animeTitle,
                coverUrl = route.coverUrl,
                episodeNumber = route.episodeNumber,
                onBack = { navController.popBackStack() },
                onNextEpisode = if (route.nextEpisodeId > 0) {
                    {
                        navController.navigate(
                            route.copy(
                                episodeId = route.nextEpisodeId,
                                episodeNumber = route.nextEpisodeNumber,
                                title = "${route.animeTitle} - EP ${route.nextEpisodeNumber}",
                                // Clear next/prev since we don't know from here
                                nextEpisodeId = -1,
                                prevEpisodeId = route.episodeId,
                                prevEpisodeNumber = route.episodeNumber,
                            )
                        ) {
                            popUpTo<Player> { inclusive = true }
                        }
                    }
                } else null,
                onPreviousEpisode = if (route.prevEpisodeId > 0) {
                    {
                        navController.navigate(
                            route.copy(
                                episodeId = route.prevEpisodeId,
                                episodeNumber = route.prevEpisodeNumber,
                                title = "${route.animeTitle} - EP ${route.prevEpisodeNumber}",
                                nextEpisodeId = route.episodeId,
                                nextEpisodeNumber = route.episodeNumber,
                                prevEpisodeId = -1,
                            )
                        ) {
                            popUpTo<Player> { inclusive = true }
                        }
                    }
                } else null,
            )
        }

        composable<Settings> {
            SettingsScreen(onBack = { navController.popBackStack() })
        }
    }
}
