#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys

def get_outputs():
    """Get active output monitors with their names and X positions."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_outputs']).decode('utf-8')
        outputs = json.loads(output)
        # Filter active outputs and sort them by their X position
        active_outputs = [o for o in outputs if o['active']]
        sorted_outputs = sorted(active_outputs, key=lambda k: k['rect']['x'])
        return [output['name'] for output in sorted_outputs]
    except Exception as e:
        print(f"Error getting outputs: {e}")
        sys.exit(1)

def move_to_monitor(target, position, target_type):
    """Move the specified workspace or window to a monitor (left, middle, right)."""
    monitors = get_outputs()
    target_monitor = None
    
    if position == "left":
        target_monitor = monitors[0]
    elif position == "right":
        target_monitor = monitors[-1]
    elif position == "middle":
        target_monitor = monitors[(len(monitors) - 1) // 2]
    else:
        print("Invalid position or not enough monitors.")
        sys.exit(1)

    if target_type == "workspace":
        try:
            print(target, target_monitor)
            subprocess.run(['i3-msg', 'workspace', target])
            subprocess.run(['i3-msg', 'move', 'workspace', 'to', 'output', target_monitor])
            # subprocess.run(['i3-msg', 'workspace', target, 'output', target_monitor])
        except Exception as e:
            print(f"Error moving workspace: {e}")
            sys.exit(1)
    elif target_type == "window":
        try:
            subprocess.run(['i3-msg', 'focus', target])
            subprocess.run(['i3-msg', 'move', 'window', 'to', 'output', target_monitor])
        except Exception as e:
            print(f"Error moving window: {e}")
            sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Move an i3 workspace or window to a specified monitor.")
    parser.add_argument("target", help="The workspace number/name or window to move.")
    parser.add_argument("position", choices=["left", "middle", "right"], help="The monitor position to move the target to.")
    parser.add_argument("--type", choices=["workspace", "window"], default="workspace", help="The type of target to move (default is workspace).")
    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_arguments()
    move_to_monitor(args.target, args.position, args.type)
