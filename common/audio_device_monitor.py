import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal
import platform

try:
    from common.subprocess_helper import run_subprocess
except ImportError:
    from subprocess import run as run_subprocess

class AudioDeviceMonitor(QObject):

    devices_changed = pyqtSignal(list)
    device_disconnected = pyqtSignal(str)
    
    def __init__(self, audio_manager, check_interval=5):
        super().__init__()
        self.audio_manager = audio_manager
        self.check_interval = check_interval
        self.current_devices = []
        self.running = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        if self.running:
            return
            
        self.running = True
        self.current_devices = self.audio_manager.get_audio_devices()
        self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
            
    def _monitor_devices(self):
        while self.running:
            try:
                current_devices = self.audio_manager.get_audio_devices()
                
                if set(current_devices) != set(self.current_devices):
                    disconnected_devices = [device for device in self.current_devices 
                                           if device not in current_devices]
                    
                    for device in disconnected_devices:
                        self.device_disconnected.emit(device)
                    
                    self.current_devices = current_devices

                    self.devices_changed.emit(current_devices)
            except Exception as e:
                print(f"Audio Device Monitor Error: {e}")
                
            time.sleep(self.check_interval)
            
    def check_device_availability(self, selected_devices):
        current_devices = self.audio_manager.get_audio_devices()
        unavailable_devices = []
        
        for device_name, _ in selected_devices:
            device_available = False
            for current_device in current_devices:
                if device_name == current_device:
                    device_available = True
                    break
            
            if not device_available:
                unavailable_devices.append(device_name)
                
        return len(unavailable_devices) == 0, unavailable_devices