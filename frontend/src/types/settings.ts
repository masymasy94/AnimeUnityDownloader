export interface Settings {
  download_dir: string;
  host_download_path: string;
  max_concurrent_downloads: number;
  plex_url: string;
  plex_token: string;
  plex_library_id: string;
}

export interface SettingsUpdate {
  download_dir?: string;
  max_concurrent_downloads?: number;
  plex_url?: string;
  plex_token?: string;
  plex_library_id?: string;
}
