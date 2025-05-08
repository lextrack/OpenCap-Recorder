import subprocess
from PyQt6.QtWidgets import QMessageBox
from base.audio_manager_base import AudioManagerBase

class LinuxAudioManager(AudioManagerBase):
    def get_audio_devices(self):
        devices = []
        cmd = ["pactl", "list", "sources"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            lines = result.stdout.splitlines()
            current_device = None
            for line in lines:
                if "Name:" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        current_device = parts[1]
                elif "Description:" in line and current_device:
                    description = line.split(":", 1)[1].strip()
                    normalized_name = self._normalize_audio_device_name(current_device)
                    devices.append(f"{description} ({normalized_name})")
                    current_device = None
            
            return devices
            
        except Exception as e:
            print(f"Error getting audio devices: {e}")
            return []
    
    def check_device_exists(self, device_name):
        devices = self.get_audio_devices()
        return device_name in devices
    
    def _normalize_audio_device_name(self, audio_device):
        encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                if isinstance(audio_device, bytes):
                    return audio_device.decode(encoding)
                else:
                    return audio_device.encode(encoding).decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
                
        return audio_device