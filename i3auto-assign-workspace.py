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

def get_outputs_with_positions():
    """Get active output monitors with their names, X and Y positions."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_outputs']).decode('utf-8')
        outputs = json.loads(output)
        # Filter active outputs
        active_outputs = [o for o in outputs if o['active']]
        return active_outputs
    except Exception as e:
        print(f"Error getting outputs: {e}")
        sys.exit(1)

def get_workspace_info(workspace_name):
    """Get information about a specific workspace."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_workspaces']).decode('utf-8')
        workspaces = json.loads(output)
        for ws in workspaces:
            if ws['name'] == workspace_name or str(ws['num']) == str(workspace_name):
                return ws
        return None
    except Exception as e:
        print(f"Error getting workspace info: {e}")
        return None

def move_to_monitor(target, position, target_type):
    """Move the specified workspace or window to a monitor (left, middle, right, down)."""
    monitors = get_outputs()
    target_monitor = None
    
    if position == "left":
        target_monitor = monitors[0]
    elif position == "right":
        target_monitor = monitors[-1]
    elif position == "middle":
        target_monitor = monitors[(len(monitors) - 1) // 2]
    elif position == "down":
        # Get monitors with full position information
        monitors_with_pos = get_outputs_with_positions()
        if monitors_with_pos:
            # Find the monitor with the highest Y position (lowest on screen)
            lowest_monitor = max(monitors_with_pos, key=lambda m: m['rect']['y'])
            target_monitor = lowest_monitor['name']
        else:
            # Fallback to middle if no monitors found
            target_monitor = monitors[(len(monitors) - 1) // 2]
    else:
        print("Invalid position or not enough monitors.")
        sys.exit(1)

    if target_type == "workspace":
        try:
            print(f"Moving workspace '{target}' to monitor '{target_monitor}'")
            
            # First, check if the workspace exists
            ws_info = get_workspace_info(target)
            
            if ws_info and ws_info['output'] == target_monitor:
                # Workspace is already on the target monitor, just switch to it
                print(f"Workspace already on {target_monitor}, switching to it")
                result = subprocess.run(['i3-msg', 'workspace', target], capture_output=True, text=True)
                print(f"Switch result: {result.stdout.strip()}")
            else:
                # Use array format for proper argument handling, especially with spaces
                # First switch to the workspace (creates it if it doesn't exist)
                result1 = subprocess.run(['i3-msg', 'workspace', target], capture_output=True, text=True)
                if result1.returncode != 0:
                    print(f"Error switching to workspace: {result1.stderr}")
                    sys.exit(1)
                print(f"Switch result: {result1.stdout.strip()}")
                
                # Then move it to the target output
                result2 = subprocess.run(['i3-msg', 'move', 'workspace', 'to', 'output', target_monitor], 
                                       capture_output=True, text=True)
                if result2.returncode != 0:
                    print(f"Error moving workspace: {result2.stderr}")
                    sys.exit(1)
                print(f"Move result: {result2.stdout.strip()}")
                
                # Focus the workspace again to ensure we're on the right monitor
                result3 = subprocess.run(['i3-msg', 'workspace', target], capture_output=True, text=True)
                print(f"Final focus result: {result3.stdout.strip()}")
                
        except subprocess.CalledProcessError as e:
            print(f"Error moving workspace: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
    elif target_type == "window":
        try:
            result1 = subprocess.run(['i3-msg', '[title="' + target + '"]', 'focus'], capture_output=True, text=True)
            if result1.returncode != 0:
                print(f"Error focusing window: {result1.stderr}")
                sys.exit(1)
            print(f"Focus result: {result1.stdout.strip()}")
            
            result2 = subprocess.run(['i3-msg', 'move', 'window', 'to', 'output', target_monitor], 
                                   capture_output=True, text=True)
            if result2.returncode != 0:
                print(f"Error moving window: {result2.stderr}")
                sys.exit(1)
            print(f"Move result: {result2.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"Error moving window: {e}")
            sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Move i3 workspaces or windows to specified monitors.",
        epilog="Examples:\n"
               "  %(prog)s 'U=left' 'V=middle' 'W=right'\n"
               "  %(prog)s 'workspace 1=left' '2=right'\n"
               "  %(prog)s --type window 'Firefox=left'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "assignments", 
        nargs='+',
        help="List of 'workspace_name=position' pairs where position is left, middle, right, or down. "
             "The string is split on the last '=' character."
    )
    parser.add_argument(
        "--type", 
        choices=["workspace", "window"], 
        default="workspace", 
        help="The type of target to move (default is workspace)."
    )
    
    args = parser.parse_args()
    return args

def parse_assignment(assignment):
    """Parse a single assignment string, splitting on the last '=' character."""
    last_eq_index = assignment.rfind('=')
    if last_eq_index == -1:
        print(f"Error: Invalid assignment format '{assignment}'. Expected 'name=position'")
        sys.exit(1)
    
    target = assignment[:last_eq_index]
    position = assignment[last_eq_index + 1:]
    
    if position not in ["left", "middle", "right", "down"]:
        print(f"Error: Invalid position '{position}' in assignment '{assignment}'. "
              f"Must be one of: left, middle, right, down")
        sys.exit(1)
    
    return target, position

if __name__ == "__main__":
    args = parse_arguments()
    
    # Process each assignment
    for assignment in args.assignments:
        target, position = parse_assignment(assignment)
        print(f"\nProcessing: {target} -> {position}")
        move_to_monitor(target, position, args.type)
