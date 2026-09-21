import os
import json
import urllib.request
import threading
import zipfile
import subprocess
import sys

GITHUB_RAW_URL = "https://raw.githubusercontent.com/YourUsername/HDPS-Repo/main/"

class GitHubUpdater:
    def __init__(self):
        self.local_versions_file = "local_versions.json"
        self.local_versions = self._load_local_versions()
        self.remote_versions = {}
        
        self.is_downloading = False
        self.download_progress = 0.0
        self.download_target = ""

    def _load_local_versions(self):
        if not os.path.exists(self.local_versions_file):
            return {}
        with open(self.local_versions_file, 'r') as f:
            return json.load(f)

    def _save_local_versions(self):
        with open(self.local_versions_file, 'w') as f:
            json.dump(self.local_versions, f, indent=4)

    def check_for_updates(self):
        try:
            url = f"{GITHUB_RAW_URL}versions.json"
            response = urllib.request.urlopen(url)
            self.remote_versions = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Could not fetch versions: {e}")
            self.remote_versions = {}

    def update_module_async(self, module_name):
        self.is_downloading = True
        self.download_target = module_name
        self.download_progress = 0.0
        
        thread = threading.Thread(target=self._download_task, args=(module_name,))
        thread.daemon = True
        thread.start()

    def _download_task(self, module_name):
        zip_save_path = os.path.join("modules", f"{module_name}.zip")
        extract_folder = os.path.join("modules", module_name)
        
        if not os.path.exists("modules"):
            os.makedirs("modules")

        file_url = f"{GITHUB_RAW_URL}modules/{module_name}.zip"
        
        try:
            print(f"\nDownloading {module_name}.zip...")
            urllib.request.urlretrieve(file_url, zip_save_path, reporthook=self._progress_hook)
            
            print(f"\nExtracting {module_name}...")
            with zipfile.ZipFile(zip_save_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
                
            if os.path.exists(zip_save_path):
                os.remove(zip_save_path)
            
            req_file = os.path.join(extract_folder, "requirements.txt")
            if os.path.exists(req_file):
                print(f"Installing missing dependencies for {module_name}...")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"]
                )
            
            self.local_versions[module_name] = self.remote_versions[module_name]
            self._save_local_versions()
            print(f"{module_name} successfully installed and configured!")
            
        except Exception as e:
            print(f"\nInstallation failed: {e}")
            
        finally:
            self.is_downloading = False

    def _progress_hook(self, block_num, block_size, total_size):
        if total_size > 0:
            downloaded = block_num * block_size
            self.download_progress = min(1.0, downloaded / total_size)