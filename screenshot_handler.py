import base64
import os
from datetime import datetime
from pathlib import Path

class ScreenshotHandler:
    def __init__(self, screenshot_dir: Path):
        self.screenshot_dir = screenshot_dir
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
    def save_screenshot(self, base64_data: str) -> dict:
        try:
            # Decode base64 data
            image_data = base64.b64decode(base64_data)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            return {
                "filename": filename,
                "path": str(filepath),
                "timestamp": timestamp
            }
        except Exception as e:
            raise Exception(f"Failed to save screenshot: {str(e)}")