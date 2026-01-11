#!/usr/bin/env -S uv run --script --with pillow
"""
Floating image viewer for X11 with rotation support
Displays images on a secondary monitor as a floating window
"""

import sys
import os
import subprocess
import re
import tempfile
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk


def get_monitor_geometry():
    """Get geometry of all monitors using xrandr"""
    try:
        output = subprocess.check_output(['xrandr', '--query'], text=True)
        monitors = []
        
        for line in output.split('\n'):
            # Match lines like: "HDMI-1 connected 1920x1080+1920+0"
            match = re.search(r'^(\S+)\s+connected\s+(\d+)x(\d+)\+(\d+)\+(\d+)', line)
            if match:
                name = match.group(1)
                width = int(match.group(2))
                height = int(match.group(3))
                x_offset = int(match.group(4))
                y_offset = int(match.group(5))
                monitors.append({
                    'name': name,
                    'width': width,
                    'height': height,
                    'x': x_offset,
                    'y': y_offset
                })
        
        return monitors
    except Exception as e:
        print(f"Warning: Could not get monitor info: {e}", file=sys.stderr)
        return None


def get_focused_monitor():
    """Get the geometry of the currently focused monitor"""
    try:
        # Get mouse position
        result = subprocess.run(['xdotool', 'getmouselocation'], 
                              capture_output=True, text=True, timeout=1)
        if result.returncode == 0:
            # Parse output like "x:1920 y:540 screen:0 window:12345"
            parts = result.stdout.split()
            mouse_x = int(parts[0].split(':')[1])
            mouse_y = int(parts[1].split(':')[1])
            
            # Find which monitor contains the mouse
            monitors = get_monitor_geometry()
            if monitors:
                for mon in monitors:
                    if (mon['x'] <= mouse_x < mon['x'] + mon['width'] and
                        mon['y'] <= mouse_y < mon['y'] + mon['height']):
                        return mon
                # Fallback to first monitor
                return monitors[0] if monitors else None
    except:
        pass
    
    # Fallback: return first monitor or None
    monitors = get_monitor_geometry()
    return monitors[0] if monitors else None


def capture_monitor(monitor=None):
    """Capture a specific monitor and return PIL Image"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_file.close()
    temp_path = temp_file.name
    
    # Delete the temp file so scrot doesn't complain about it existing
    os.unlink(temp_path)
    
    # If no monitor specified, capture current/focused monitor
    if monitor is None:
        monitor = get_focused_monitor()
    
    # Build geometry string for the capture area
    if monitor:
        geom = f"{monitor['width']}x{monitor['height']}+{monitor['x']}+{monitor['y']}"
    else:
        geom = None
    
    # Try scrot (fastest)
    try:
        if geom:
            cmd = ['scrot', '-o', '-a', f"{monitor['x']},{monitor['y']},{monitor['width']},{monitor['height']}", temp_path]
        else:
            cmd = ['scrot', '-o', temp_path]
        
        result = subprocess.run(cmd, capture_output=True, timeout=2, text=True)
        
        # scrot might create a different filename, check for variations
        actual_path = temp_path
        if not os.path.exists(temp_path):
            # Check for the _000 variation
            base = temp_path.rsplit('.', 1)[0]
            ext = temp_path.rsplit('.', 1)[1]
            actual_path = f"{base}_000.{ext}"
            
        if result.returncode == 0 and os.path.exists(actual_path) and os.path.getsize(actual_path) > 0:
            img = Image.open(actual_path)
            os.unlink(actual_path)
            return img, monitor
        
        # Clean up any created files
        for f in [temp_path, f"{temp_path.rsplit('.', 1)[0]}_000.{temp_path.rsplit('.', 1)[1]}"]:
            if os.path.exists(f):
                os.unlink(f)
                
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        print(f"scrot exception: {e}", file=sys.stderr)
    
    # Try maim (also fast) 
    try:
        if geom:
            cmd = ['maim', '-g', geom, temp_path]
        else:
            cmd = ['maim', temp_path]
        
        result = subprocess.run(cmd, capture_output=True, timeout=2, text=True)
            
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            img = Image.open(temp_path)
            os.unlink(temp_path)
            return img, monitor
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        print(f"maim exception: {e}", file=sys.stderr)
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    
    return None, None


class ScreenshotSelector:
    """Interactive screenshot selection tool"""
    def __init__(self, bg_image, monitor):
        self.bg_image = bg_image
        self.monitor = monitor
        self.cancelled = False
        self.selection = None
        
        self.root = tk.Tk()
        
        # Position on the captured monitor
        if monitor:
            self.root.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['x']}+{monitor['y']}")
        else:
            self.root.attributes('-fullscreen', True)
            
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.configure(bg='black')
        self.root.config(cursor='crosshair')
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root, 
            highlightthickness=0,
            bg='black'
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Display dimmed background (resize for faster display if very large)
        display_img = bg_image
        if bg_image.width > 3840 or bg_image.height > 2160:
            # Downsample for display speed
            display_img = bg_image.resize(
                (bg_image.width // 2, bg_image.height // 2),
                Image.Resampling.FAST
            )
        
        # Dim the image (multiply is faster than point)
        dimmed = display_img.point(lambda p: p * 0.4)
        self.photo_bg = ImageTk.PhotoImage(dimmed)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo_bg)
        
        # Create instruction label
        self.info_text = self.canvas.create_text(
            bg_image.width // 2,
            20,
            text="Click and drag to select area • ESC to cancel",
            fill='white',
            font=('sans-serif', 14, 'bold'),
            anchor='n'
        )
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Bind mouse events
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.root.bind('<Escape>', self.on_escape)
    
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='cyan', width=2
        )
    
    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_release(self, event):
        if self.start_x and self.start_y:
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            
            # Only accept selection if it has some size
            if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                self.selection = (x1, y1, x2, y2)
            
        self.root.quit()
    
    def on_escape(self, event):
        self.cancelled = True
        self.root.quit()
    
    def run(self):
        self.root.mainloop()
        self.root.destroy()
        
        if self.cancelled:
            return None
        return self.selection


def interactive_screenshot():
    """Let user select area and return screenshot"""
    # Capture the focused monitor
    bg_image, monitor = capture_monitor()
    
    if not bg_image:
        print("Error: Could not capture screen. Please install scrot or maim", file=sys.stderr)
        return None
    
    # Show selection UI
    selector = ScreenshotSelector(bg_image, monitor)
    selection = selector.run()
    
    if selection is None:
        return None
    
    # Crop from the background image we already captured
    x1, y1, x2, y2 = selection
    return bg_image.crop((x1, y1, x2, y2))


class FloatingImageViewer:
    def __init__(self, image_source, is_image=True):
        self.root = tk.Tk()
        self.root.title("Image Viewer")
        
        # Make window floating (above other windows)
        self.root.attributes('-topmost', True)
        
        # Remove window decorations for a cleaner look
        self.root.overrideredirect(True)
        
        # Load and rotate image 180 degrees
        try:
            if is_image:
                # image_source is a PIL Image
                img = image_source
            else:
                # image_source is a file path
                img = Image.open(image_source)
            
            img = img.rotate(180, expand=True)
            
            # Get monitor information
            monitors = get_monitor_geometry()
            
            if monitors and len(monitors) >= 2:
                # Use second monitor
                target_monitor = monitors[1]
                monitor_width = target_monitor['width']
                monitor_height = target_monitor['height']
                monitor_x = target_monitor['x']
                monitor_y = target_monitor['y']
            elif monitors and len(monitors) == 1:
                # Only one monitor, use right half
                target_monitor = monitors[0]
                monitor_width = target_monitor['width'] // 2
                monitor_height = target_monitor['height']
                monitor_x = target_monitor['x'] + monitor_width
                monitor_y = target_monitor['y']
            else:
                # Fallback to screen dimensions
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                monitor_width = screen_width // 2
                monitor_height = screen_height
                monitor_x = monitor_width
                monitor_y = 0
            
            # Scale image to fit monitor while maintaining aspect ratio
            # Calculate scaling factors for width and height
            img_width, img_height = img.size
            width_ratio = monitor_width / img_width
            height_ratio = monitor_height / img_height
            
            # Use the smaller ratio so entire image fits within monitor
            scale_ratio = min(width_ratio, height_ratio)
            
            new_width = int(img_width * scale_ratio)
            new_height = int(img_height * scale_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(img)
            
            # Create label with image
            self.label = tk.Label(self.root, image=self.photo, bg='black')
            self.label.pack()
            
            # Center window on target monitor
            window_width = img.width
            window_height = img.height
            
            x_pos = monitor_x + (monitor_width - window_width) // 2
            y_pos = monitor_y + (monitor_height - window_height) // 2
            
            self.root.geometry(f'{window_width}x{window_height}+{x_pos}+{y_pos}')
            
            # Bind escape key to close
            self.root.bind('<Escape>', lambda e: self.close())
            
            # Bind click to close
            self.label.bind('<Button-1>', lambda e: self.close())
            
            # Focus the window
            self.root.focus_force()
            
        except Exception as e:
            print(f"Error loading image: {e}", file=sys.stderr)
            sys.exit(1)
    
    def close(self):
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()


def close_existing_viewer():
    """Close any existing instance of this viewer"""
    pid_file = '/tmp/floating_image_viewer.pid'
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Try to kill the old process
            os.kill(old_pid, 9)
        except (ProcessLookupError, ValueError):
            # Process doesn't exist anymore
            pass
        except Exception as e:
            print(f"Warning: Could not close existing viewer: {e}", file=sys.stderr)
    
    # Write current PID
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))


def main():
    screenshot_mode = False
    image_path = None
    
    # Parse arguments
    if len(sys.argv) == 2:
        if sys.argv[1] == '--screenshot':
            screenshot_mode = True
        else:
            image_path = sys.argv[1]
    elif len(sys.argv) == 1:
        print("Usage: floating_image_viewer.py <image_path>")
        print("   or: floating_image_viewer.py --screenshot")
        sys.exit(1)
    else:
        print("Usage: floating_image_viewer.py <image_path>")
        print("   or: floating_image_viewer.py --screenshot")
        sys.exit(1)
    
    # Close existing viewer if any
    close_existing_viewer()
    
    if screenshot_mode:
        # Interactive screenshot
        img = interactive_screenshot()
        if img is None:
            print("Screenshot cancelled")
            sys.exit(0)
        
        # Create and run viewer with PIL Image
        viewer = FloatingImageViewer(img, is_image=True)
        viewer.run()
    else:
        # Load from file
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}", file=sys.stderr)
            sys.exit(1)
        
        # Create and run viewer with file path
        viewer = FloatingImageViewer(image_path, is_image=False)
        viewer.run()
    
    # Clean up PID file on exit
    try:
        os.remove('/tmp/floating_image_viewer.pid')
    except:
        pass


if __name__ == '__main__':
    main()
