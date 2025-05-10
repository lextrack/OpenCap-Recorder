import os
import sys
import subprocess
import locale
import platform
from PyQt6.QtWidgets import QMessageBox
from base.audio_manager_base import AudioManagerBase

class WindowsAudioManager(AudioManagerBase):
    def get_audio_devices(self):
        ffmpeg_path = self._get_ffmpeg_path()
        if not ffmpeg_path:
            return []
       
        cmd = [ffmpeg_path, "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True, 
                encoding='utf-8', 
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            lines = result.stderr.splitlines()
            devices = []
           
            for line in lines:
                if "audio" in line and len(line.split("\"")) > 1:
                    device_name = line.split("\"")[1]
                    normalized_name = self._normalize_audio_device_name(device_name)
                    devices.append(normalized_name)
            
            return devices
            
        except subprocess.CalledProcessError as e:
            print(f"Error running FFmpeg (Audio): {e}")
            return []
        except FileNotFoundError:
            print(f"FFmpeg (Audio) not found at {ffmpeg_path}")
            return []
        except Exception as e:
            print(f"Unexpected error getting audio devices: {e}")
            return []
           
    def _normalize_audio_device_name(self, audio_device):
        system_encoding = locale.getpreferredencoding()
        
        encodings_to_try = [system_encoding, 'utf-8', 'cp1252', 'latin-1']
        
        for encoding in encodings_to_try:
            try:
                if isinstance(audio_device, bytes):
                    return audio_device.decode(encoding)
                else:
                    return audio_device
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue

        if isinstance(audio_device, bytes):
            return audio_device.decode('utf-8', errors='replace')
        return audio_device
    
    def check_device_exists(self, device_name):
        devices = self.get_audio_devices()
        return device_name in devices
    
    def _get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        ffmpeg_path = os.path.join(base_path, 'ffmpeg_files', 'ffmpeg.exe')
        
        return ffmpeg_path if os.path.exists(ffmpeg_path) else None