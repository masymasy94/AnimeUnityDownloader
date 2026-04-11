package com.hasasiero.tvstream.data.local

import androidx.room.*

@Entity(tableName = "watch_history")
data class WatchHistoryEntry(
    @PrimaryKey val episodeId: Int,
    val animeId: Int,
    val animeSlug: String,
    val animeTitle: String,
    val coverUrl: String?,
    val sourceSite: String,
    val episodeNumber: String,
    val episodeTitle: String?,
    val positionMs: Long = 0,
    val durationMs: Long = 0,
    val lastWatchedAt: Long = System.currentTimeMillis(),
)

@Dao
interface WatchHistoryDao {
    @Query("SELECT * FROM watch_history ORDER BY lastWatchedAt DESC LIMIT 20")
    suspend fun getRecent(): List<WatchHistoryEntry>

    @Query("SELECT * FROM watch_history WHERE episodeId = :episodeId LIMIT 1")
    suspend fun getByEpisodeId(episodeId: Int): WatchHistoryEntry?

    @Upsert
    suspend fun upsert(entry: WatchHistoryEntry)
}

@Database(entities = [WatchHistoryEntry::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun watchHistoryDao(): WatchHistoryDao
}
