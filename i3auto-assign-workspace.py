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

def workspace_exists(workspace_name):
    """Check if a workspace exists."""
    return get_workspace_info(workspace_name) is not None

def get_target_monitor(position):
    """Get the target monitor name based on position (left, middle, right, down)."""
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
    
    return target_monitor

def move_to_monitor(target, position, target_type):
    """Move the specified workspace or window to a monitor (left, middle, right, down)."""
    target_monitor = get_target_monitor(position)

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

def focus_monitor(position):
    """Focus a monitor based on position (left, middle, right, down)."""
    target_monitor = get_target_monitor(position)
    
    try:
        # Focus the monitor by using focus output command
        result = subprocess.run(['i3-msg', 'focus', 'output', target_monitor], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error focusing monitor: {result.stderr}")
            return False
        print(f"Focused monitor: {target_monitor}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error focusing monitor: {e}")
        return False

def open_workspace(workspace_name, position):
    """Open or focus a workspace on a specific monitor."""
    if workspace_exists(workspace_name):
        # Workspace exists, just focus it
        try:
            print(f"Workspace '{workspace_name}' exists, focusing it")
            result = subprocess.run(['i3-msg', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error focusing workspace: {result.stderr}")
                sys.exit(1)
            print(f"Focused workspace: {workspace_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error focusing workspace: {e}")
            sys.exit(1)
    else:
        # Workspace doesn't exist, focus monitor first then create workspace
        print(f"Workspace '{workspace_name}' doesn't exist, creating on {position} monitor")
        
        # Focus the target monitor first
        if not focus_monitor(position):
            sys.exit(1)
        
        # Now create/switch to the workspace on the focused monitor
        try:
            result = subprocess.run(['i3-msg', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error creating workspace: {result.stderr}")
                sys.exit(1)
            print(f"Created and focused workspace: {workspace_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating workspace: {e}")
            sys.exit(1)

def move_container_to_workspace(workspace_name, position):
    """Move the focused container to a workspace on a specific monitor and follow focus."""
    if workspace_exists(workspace_name):
        # Workspace exists, just move container to it
        try:
            print(f"Moving focused container to existing workspace '{workspace_name}'")
            result = subprocess.run(['i3-msg', 'move', 'container', 'to', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error moving container to workspace: {result.stderr}")
                sys.exit(1)
            print(f"Container moved to workspace: {workspace_name}")
            
            # Follow the container to the workspace
            result = subprocess.run(['i3-msg', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error focusing workspace: {result.stderr}")
                sys.exit(1)
            print(f"Focused workspace: {workspace_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error moving container to workspace: {e}")
            sys.exit(1)
    else:
        # Workspace doesn't exist, create it on the correct monitor first
        print(f"Workspace '{workspace_name}' doesn't exist, creating on {position} monitor")
        
        # Focus the target monitor first
        if not focus_monitor(position):
            sys.exit(1)
        
        # Create the workspace on the focused monitor by switching to it
        try:
            result = subprocess.run(['i3-msg', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error creating workspace: {result.stderr}")
                sys.exit(1)
            print(f"Created workspace '{workspace_name}' on {position} monitor")
        except subprocess.CalledProcessError as e:
            print(f"Error creating workspace: {e}")
            sys.exit(1)
        
        # Now move the container to the newly created workspace
        try:
            # Move the container to the workspace we just created
            result = subprocess.run(['i3-msg', 'move', 'container', 'to', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error moving container to workspace: {result.stderr}")
                sys.exit(1)
            print(f"Container moved to new workspace: {workspace_name}")
            
            # Focus the workspace to follow the container
            result = subprocess.run(['i3-msg', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error focusing workspace: {result.stderr}")
                sys.exit(1)
            print(f"Focused workspace: {workspace_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error moving container to workspace: {e}")
            sys.exit(1)

def find_window_by_class_or_title(program_name):
    """Find windows by class or title matching the program name (case-insensitive)."""
    try:
        # Get all windows using i3-msg
        output = subprocess.check_output(['i3-msg', '-t', 'get_tree']).decode('utf-8')
        tree = json.loads(output)
        
        def find_windows_recursive(node, windows_by_class, windows_by_title):
            """Recursively search for windows in the i3 tree."""
            if 'window' in node and node['window'] is not None:
                # This is a window node
                window_class = node.get('window_properties', {}).get('class', '').lower()
                window_title = node.get('name', '').lower()
                window_instance = node.get('window_properties', {}).get('instance', '').lower()
                
                program_lower = program_name.lower()
                
                window_info = {
                    'id': node['window'],
                    'class': window_class,
                    'title': window_title,
                    'instance': window_instance,
                    'focused': node.get('focused', False)
                }
                
                # First priority: match in class or instance
                if program_lower in window_class or program_lower in window_instance:
                    windows_by_class.append(window_info)
                # Second priority: match in title (only if not already matched by class)
                elif program_lower in window_title:
                    windows_by_title.append(window_info)
            
            # Recursively search child nodes
            for child in node.get('nodes', []):
                find_windows_recursive(child, windows_by_class, windows_by_title)
            for child in node.get('floating_nodes', []):
                find_windows_recursive(child, windows_by_class, windows_by_title)
        
        windows_by_class = []
        windows_by_title = []
        find_windows_recursive(tree, windows_by_class, windows_by_title)
        
        # Return class matches first, then title matches if no class matches found
        if windows_by_class:
            return prioritize_main_windows(windows_by_class)
        else:
            return prioritize_main_windows(windows_by_title)
        
    except Exception as e:
        print(f"Error finding windows: {e}")
        return []

def prioritize_main_windows(windows):
    """Prioritize main program windows over debug/run/tool windows."""
    if not windows:
        return windows
    
    # Keywords that indicate secondary/tool windows
    secondary_keywords = ['debug', 'run', 'console', 'terminal', 'log', 'output', 'tool', 'toolbox']
    
    # Separate main windows from secondary windows
    main_windows = []
    secondary_windows = []
    
    for window in windows:
        title_lower = window['title'].lower()
        is_secondary = any(keyword in title_lower for keyword in secondary_keywords)
        
        if is_secondary:
            secondary_windows.append(window)
        else:
            main_windows.append(window)
    
    # Return main windows first, then secondary windows if no main windows found
    if main_windows:
        return main_windows
    else:
        return secondary_windows

def focus_window_by_id(window_id):
    """Focus a window by its ID."""
    try:
        result = subprocess.run(['i3-msg', f'[id="{window_id}"]', 'focus'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error focusing window: {result.stderr}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error focusing window: {e}")
        return False

def launch_program_detached(program_name, workspace_name):
    """Launch a program in detached mode on a specific workspace."""
    try:
        # Use i3-msg exec to launch the program on the current workspace
        # This ensures the program opens on the workspace we just focused
        result = subprocess.run([
            'i3-msg', 'exec', '--no-startup-id', program_name
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error launching program with i3-msg: {result.stderr}")
            # Fallback to direct launch
            subprocess.Popen([program_name], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL, 
                            stdin=subprocess.DEVNULL,
                            start_new_session=True)
        
        print(f"Launched program: {program_name} on workspace: {workspace_name}")
        return True
    except Exception as e:
        print(f"Error launching program '{program_name}': {e}")
        return False

def find_and_focus_program(program_name, workspace_name, position):
    """Find and focus a program, or launch it on the specified workspace if not found."""
    # First, try to find the program among open windows
    windows = find_window_by_class_or_title(program_name)
    
    if windows:
        # Program found, focus the first match
        window = windows[0]  # Focus the first matching window
        print(f"Found {program_name} (class: '{window['class']}', title: '{window['title']}')")
        if focus_window_by_id(window['id']):
            print(f"Focused {program_name}")
        else:
            print(f"Failed to focus {program_name}")
            sys.exit(1)
    else:
        # Program not found, launch it on the specified workspace
        print(f"{program_name} not found, launching on workspace '{workspace_name}' ({position} monitor)")
        
        # Use the existing open_workspace function to focus/create the workspace
        open_workspace(workspace_name, position)
        
        # Launch the program detached
        if not launch_program_detached(program_name, workspace_name):
            sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Manage i3 workspaces and monitors.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # move-ws-to-monitor subcommand
    move_parser = subparsers.add_parser(
        'move-ws-to-monitor',
        help='Move workspaces or windows to specified monitors',
        epilog="Examples:\n"
               "  %(prog)s 'U=left' 'V=middle' 'W=right'\n"
               "  %(prog)s 'workspace 1=left' '2=right'\n"
               "  %(prog)s --type window 'Firefox=left'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    move_parser.add_argument(
        "assignments", 
        nargs='+',
        help="List of 'workspace_name=position' pairs where position is left, middle, right, or down. "
             "The string is split on the last '=' character."
    )
    move_parser.add_argument(
        "--type", 
        choices=["workspace", "window"], 
        default="workspace", 
        help="The type of target to move (default is workspace)."
    )
    
    # open-ws subcommand
    open_parser = subparsers.add_parser(
        'open-ws',
        help='Open or focus a workspace on a specific monitor',
        epilog="Examples:\n"
               "  %(prog)s 'MyWorkspace=left'\n"
               "  %(prog)s '3=middle'\n"
               "  %(prog)s 'Terminal=down'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    open_parser.add_argument(
        "assignment",
        help="A single 'workspace_name=position' pair where position is left, middle, right, or down. "
             "The string is split on the last '=' character."
    )
    
    # move-container-to-ws subcommand
    container_parser = subparsers.add_parser(
        'move-container-to-ws',
        help='Move the focused container to a workspace on a specific monitor',
        epilog="Examples:\n"
               "  %(prog)s 'MyWorkspace=left'\n"
               "  %(prog)s '3=middle'\n"
               "  %(prog)s 'Terminal=down'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    container_parser.add_argument(
        "assignment",
        help="A single 'workspace_name=position' pair where position is left, middle, right, or down. "
             "The string is split on the last '=' character."
    )
    
    # find-and-focus subcommand
    focus_parser = subparsers.add_parser(
        'find-and-focus',
        help='Find and focus a program, or launch it on a specific workspace if not found',
        epilog="Examples:\n"
               "  %(prog)s firefox 'Browser=left'\n"
               "  %(prog)s pycharm 'IDE=middle'\n"
               "  %(prog)s idea 'Development=right'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    focus_parser.add_argument(
        "program_name",
        help="The name of the program to find and focus (e.g., 'firefox', 'pycharm', 'idea')"
    )
    focus_parser.add_argument(
        "workspace_assignment",
        help="A 'workspace_name=position' pair for where to launch the program if not found. "
             "Position is left, middle, right, or down. The string is split on the last '=' character."
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
    
    if args.command == 'move-ws-to-monitor':
        # Process each assignment for move-ws-to-monitor
        for assignment in args.assignments:
            target, position = parse_assignment(assignment)
            print(f"\nProcessing: {target} -> {position}")
            move_to_monitor(target, position, args.type)
    elif args.command == 'open-ws':
        # Process single assignment for open-ws
        target, position = parse_assignment(args.assignment)
        print(f"Opening workspace: {target} on {position} monitor")
        open_workspace(target, position)
    elif args.command == 'move-container-to-ws':
        # Process single assignment for move-container-to-ws
        target, position = parse_assignment(args.assignment)
        print(f"Moving focused container to workspace: {target} on {position} monitor")
        move_container_to_workspace(target, position)
    elif args.command == 'find-and-focus':
        # Process find-and-focus command
        workspace_name, position = parse_assignment(args.workspace_assignment)
        print(f"Finding and focusing program: {args.program_name}")
        find_and_focus_program(args.program_name, workspace_name, position)
    else:
        print("No command specified. Use --help to see available commands.")
        sys.exit(1)
