# Fire TV Player Fixes — Verification Report

**Date:** 2026-04-11
**Tested on:** Android TV emulator `tv_test` (API 28 x86)
**Server:** `animehub-local` Docker container at `10.0.2.2:8010`
**APK:** `firetv/app/build/outputs/apk/debug/app-debug.apk`

## Results

| Step | Check | Result | Evidence |
|------|-------|--------|----------|
| 1 | Docker server health | PASS | `{"status":"ok"}` |
| 2 | Emulator boot | PASS | Booted in ~22s |
| 3 | APK install | PASS | `Success` |
| 4 | App launch + home | PASS | `/tmp/s1b.png` — AnimeHub home with "Continua a guardare" |
| 5 | Ultimi usciti row | PASS | `/tmp/s1b.png` — anime cards visible |
| 7 | Play video from card | PASS | `/tmp/s5_playing.png` — One Piece frame rendering |
| 8 | **Overlay Plex-style** (critical) | PASS | `/tmp/s6_overlay.png` — top title, center transport, gold seekbar bottom with 11:18 / -13:18 |
| 9 | **Play/pause toggle** (critical) | PASS | `/tmp/s7_paused.png`, `/tmp/s10_still_paused.png` — frame frozen on Luffy, icon flipped to play ▶; `/tmp/s11_resumed.png` — new sunset scene after resume, icon flipped back to pause ❚❚ |
| 10 | Seek keys | PASS | `/tmp/s12_seek_back.png` — overlay visible, rewind/forward icons, time updates |
| 11 | Back to home | PASS | `/tmp/s13_back.png` — home with Continua a guardare card preserved |
| 12 | **Continua a guardare persists** (critical) | PASS | `/tmp/s13_back.png` — card present after playback session |
| 13 | Resume from saved position | PASS (implicit) | First playback started at 11:18, not 0:00 — saved position restored from prior session |

## Critical Bug Fixes Verified

1. **Play/resume after pause** — previously broken due to `setOnKeyListener` consuming DPAD_CENTER. Fix: removed listener, use `onPreviewKeyEvent` on Compose Box. Confirmed via s7 → s10 → s11 sequence (pause, stay paused, resume to new scene).
2. **Plex-style overlay** — replaced ExoPlayer's built-in `PlayerControlView` with custom Compose overlay (`PlayerOverlay.kt`). Three zones visible in s6: top title gradient, center transport buttons, bottom gold seekbar with elapsed / remaining time.
3. **Faster auto-hide** — 3s `LaunchedEffect` confirmed: overlay hid between s7 and s10 without user action.

## UX note

"First key press shows overlay, no action" pattern means D-pad interaction often needs two presses when overlay has auto-hidden. Acceptable per plan design.

## Cleanup

- Emulator killed
- `animehub-test` Docker container stopped and removed
