import PyQt6.QtWidgets as qtw
import platform
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from common.logging_config import setup_logging

logger = setup_logging()

def main():
    logger.info(f"Starting OpenCap Recorder on {platform.system()} platform.")
   
    app = qtw.QApplication(sys.argv)
   
    if platform.system() == 'Windows':
        from platforms.windows_recorder import WindowsRecorder
        recorder = WindowsRecorder()
    elif platform.system() == 'Linux':
        from platforms.linux_recorder import LinuxRecorder
        recorder = LinuxRecorder()
    else:
        error_msg = f"Platform not supported: {platform.system()}"
        logger.error(error_msg)
        raise NotImplementedError(error_msg)
   
    recorder.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        print(f"Error: {e}")
        
        app = qtw.QApplication.instance()
        if app is None:
            app = qtw.QApplication(sys.argv)
        
        error_dialog = qtw.QMessageBox()
        error_dialog.setIcon(qtw.QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("An unexpected error has occurred")
        error_dialog.setDetailedText(str(e))
        error_dialog.exec()