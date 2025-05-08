from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QDialog)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QImage, QPixmap, QFont
import mss
import cv2
import numpy as np

class AreaSelector:
    def __init__(self, parent):
        self.parent = parent
        
    def select_area(self, callback):
        self.callback = callback
        self.dialog = AreaSelectorDialog(self.parent)
        self.dialog.finished.connect(self.handle_result)
        self.dialog.exec()
    
    def handle_result(self, result):
        if hasattr(self.dialog, 'record_area'):
            self.callback(self.dialog.record_area)
        else:
            self.callback(None)


class AreaSelectorDialog(QDialog):
    def __init__(self, parent):
        super().__init__(None)
        self.parent = parent
        self.record_area = None
        self.rect = None
        self.start_pos = None
        self.current_pos = None
        self.is_dragging = False
        self.background_image = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(False)

        self.coord_font = QFont("Arial", 14, QFont.Weight.Bold)

        self.setMouseTracking(True)
        
        self.parent.hide()
        
        self.take_screenshot()
        
    def take_screenshot(self):
        screen = self.screen()
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)
        
        with mss.mss() as sct:
            # Get the entire screen dimensions
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            img_array = np.array(screenshot)
            
            # Convert to RGB format for Qt
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)
            
            # Create QImage from array
            h, w, ch = img_array.shape
            bytes_per_line = ch * w
            q_img = QImage(img_array.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Convert to pixmap
            self.background_image = QPixmap.fromImage(q_img)
        
        # Show in fullscreen
        self.showFullScreen()
        self.raise_()  # Bring to front
        self.activateWindow()  # Give focus

    def paintEvent(self, event):
        """Paint the selection overlay"""
        if not self.background_image:
            return
            
        painter = QPainter(self)
        
        # Draw background image
        painter.drawPixmap(0, 0, self.background_image)
        
        # Draw dark overlay
        overlay = QColor(0, 0, 0, 128)
        painter.fillRect(0, 0, self.width(), self.height(), overlay)
        
        # Draw selection rectangle if exists
        if self.start_pos and self.current_pos and self.is_dragging:
            rect = QRect(self.start_pos, self.current_pos).normalized()
            
            # Clear the selection area (remove overlay)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # Draw selection rectangle border
            pen = QPen(QColor(255, 0, 0), 2)  # Red border
            painter.setPen(pen)
            painter.drawRect(rect)
            
            # Draw corner markers
            marker_size = 6
            marker_color = QColor(255, 255, 0)  # Yellow
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setBrush(QBrush(marker_color))
            
            # Draw markers at corners
            corners = [
                QPoint(rect.left(), rect.top()),
                QPoint(rect.right(), rect.top()),
                QPoint(rect.left(), rect.bottom()),
                QPoint(rect.right(), rect.bottom())
            ]
            
            for corner in corners:
                painter.drawRect(
                    corner.x() - marker_size,
                    corner.y() - marker_size,
                    marker_size * 2,
                    marker_size * 2
                )
            
            # Draw dimensions text
            if rect.width() > 60 and rect.height() > 40:
                dimension_text = f"{rect.width()} × {rect.height()} px"
                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.setPen(QPen(QColor(255, 255, 255)))
                # Center the text in the rectangle
                text_rect = painter.boundingRect(rect, Qt.AlignmentFlag.AlignCenter, dimension_text)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, dimension_text)
        
        # Draw crosshair if not dragging
        if not self.is_dragging and self.current_pos:
            pen = QPen(QColor(0, 255, 255), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            
            # Horizontal line
            painter.drawLine(0, self.current_pos.y(), self.width(), self.current_pos.y())
            # Vertical line
            painter.drawLine(self.current_pos.x(), 0, self.current_pos.x(), self.height())

    def mouseMoveEvent(self, event):
        """Handle mouse movement"""
        self.current_pos = event.pos()
        
        if self.is_dragging:
            self.update()
        else:
            self.update()

    def mousePressEvent(self, event):
        """Handle mouse press (start selection)"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.start_pos = event.pos()
            self.current_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """Handle mouse release (end selection)"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            end_pos = event.pos()
            
            if self.start_pos:
                # Get the selection rectangle
                rect = QRect(self.start_pos, end_pos).normalized()
                
                # Check if selection is valid
                if rect.width() > 10 and rect.height() > 10:
                    x1, y1 = rect.left(), rect.top()
                    x2, y2 = rect.right(), rect.bottom()
                    
                    # Ensure even dimensions
                    width = x2 - x1
                    height = y2 - y1
                    
                    if width % 2 == 1:
                        x2 += 1
                    if height % 2 == 1:
                        y2 += 1
                    
                    self.record_area = (x1, y1, x2, y2)
                else:
                    self.record_area = None
                
                self.finish_selection()

    def keyPressEvent(self, event):
        """Handle escape key to cancel selection"""
        if event.key() == Qt.Key.Key_Escape:
            self.record_area = None
            self.finish_selection()

    def finish_selection(self):
        """Clean up and return to parent"""
        self.close()
        self.parent.show()
        self.accept()