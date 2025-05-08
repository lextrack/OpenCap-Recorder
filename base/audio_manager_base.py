import abc
import locale

class AudioManagerBase(abc.ABC):
    def __init__(self):
        self.audio_devices = self.get_audio_devices()
        
    @abc.abstractmethod
    def get_audio_devices(self):
        pass
        
    def _normalize_audio_device_name(self, audio_device):
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']

        for encoding in encodings_to_try:
            try:
                audio_device = audio_device.encode(encoding).decode('utf-8')
                break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            
        return audio_device
        
    def refresh_devices(self):
        self.audio_devices = self.get_audio_devices()