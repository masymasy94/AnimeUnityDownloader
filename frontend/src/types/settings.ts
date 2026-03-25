export interface Settings {
  download_dir: string;
  host_download_path: string;
  max_concurrent_downloads: number;
}

export interface SettingsUpdate {
  download_dir?: string;
  max_concurrent_downloads?: number;
}
