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

def get_primary_monitor():
    """Get the primary monitor (marked as primary in i3)."""
    try:
        outputs = get_outputs_with_positions()
        for output in outputs:
            if output.get('primary', False):
                return output
        # If no primary is marked, return the first active output
        if outputs:
            return outputs[0]
        return None
    except Exception as e:
        print(f"Error getting primary monitor: {e}")
        return None

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
    """Get the target monitor name based on position (left, middle, right, down).
    
    'middle' is always the primary monitor.
    'left' is the monitor to the left of primary, fallback to middle if not exists.
    'right' is the monitor to the right of primary, fallback to middle if not exists.
    'down' is the monitor below primary, fallback to middle if not exists.
    """
    primary = get_primary_monitor()
    if not primary:
        print("Error: No monitors found")
        sys.exit(1)
    
    # Middle is always the primary monitor
    if position == "middle":
        return primary['name']
    
    # Get all monitors with positions
    monitors = get_outputs_with_positions()
    primary_x = primary['rect']['x']
    primary_y = primary['rect']['y']
    primary_width = primary['rect']['width']
    primary_height = primary['rect']['height']
    
    if position == "left":
        # Find monitor to the left of primary (x < primary_x)
        left_monitors = [m for m in monitors if m['rect']['x'] < primary_x]
        if left_monitors:
            # Get the rightmost of the left monitors (closest to primary)
            target = max(left_monitors, key=lambda m: m['rect']['x'])
            return target['name']
        else:
            # No monitor to the left, fallback to middle
            return primary['name']
    
    elif position == "right":
        # Find monitor to the right of primary (x > primary_x + primary_width/2)
        # and roughly at the same vertical level (not significantly below)
        right_monitors = []
        for m in monitors:
            if m['name'] == primary['name']:
                continue
            # Check if monitor is to the right
            if m['rect']['x'] >= primary_x + primary_width:
                # Check if it's at roughly the same vertical level (not a "down" monitor)
                # Allow some vertical offset but not a full monitor height difference
                vertical_offset = abs(m['rect']['y'] - primary_y)
                if vertical_offset < primary_height * 0.5:  # Less than half the height offset
                    right_monitors.append(m)
        
        if right_monitors:
            # Get the leftmost of the right monitors (closest to primary)
            target = min(right_monitors, key=lambda m: m['rect']['x'])
            return target['name']
        else:
            # No monitor to the right, fallback to middle
            return primary['name']
    
    elif position == "down":
        # Find monitor below primary (y significantly greater than primary_y)
        # Must be actually below, not just slightly offset
        down_monitors = []
        for m in monitors:
            if m['name'] == primary['name']:
                continue
            # Check if monitor is below (y position is at least half the primary height below)
            if m['rect']['y'] >= primary_y + primary_height * 0.5:
                down_monitors.append(m)
        
        if down_monitors:
            # Get the topmost of the down monitors (closest to primary)
            target = min(down_monitors, key=lambda m: m['rect']['y'])
            return target['name']
        else:
            # No monitor below, fallback to middle
            return primary['name']
    
    else:
        print("Invalid position. Must be one of: left, middle, right, down")
        sys.exit(1)

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
        # Workspace doesn't exist, move container and create it on the correct monitor
        print(f"Workspace '{workspace_name}' doesn't exist, creating on {position} monitor")
        
        # Move the container to the new workspace first (this creates the workspace)
        try:
            result = subprocess.run(['i3-msg', 'move', 'container', 'to', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error moving container to workspace: {result.stderr}")
                sys.exit(1)
            print(f"Container moved to new workspace: {workspace_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error moving container to workspace: {e}")
            sys.exit(1)
        
        # Now move the workspace (with the container) to the correct monitor
        try:
            target_monitor = get_target_monitor(position)
            result = subprocess.run(['i3-msg', 'workspace', workspace_name], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error focusing new workspace: {result.stderr}")
                sys.exit(1)
            
            result = subprocess.run(['i3-msg', 'move', 'workspace', 'to', 'output', target_monitor], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error moving workspace to monitor: {result.stderr}")
                sys.exit(1)
            print(f"Moved workspace '{workspace_name}' to {position} monitor ({target_monitor})")
        except subprocess.CalledProcessError as e:
            print(f"Error positioning workspace: {e}")
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

def get_current_monitor():
    """Get the name of the currently focused monitor."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_workspaces']).decode('utf-8')
        workspaces = json.loads(output)
        for ws in workspaces:
            if ws['focused']:
                return ws['output']
        return None
    except Exception as e:
        print(f"Error getting current monitor: {e}")
        return None

def get_current_workspace():
    """Get the name of the currently focused workspace."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_workspaces']).decode('utf-8')
        workspaces = json.loads(output)
        for ws in workspaces:
            if ws['focused']:
                return ws['name']
        return None
    except Exception as e:
        print(f"Error getting current workspace: {e}")
        return None

def get_window_workspace_and_monitor(window_id):
    """Get the workspace and monitor for a given window ID."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_tree']).decode('utf-8')
        tree = json.loads(output)
        
        def find_window_info(node, current_output=None, current_workspace=None):
            """Recursively find window information."""
            # Track current output and workspace as we traverse
            if node.get('type') == 'output':
                current_output = node.get('name')
            elif node.get('type') == 'workspace':
                current_workspace = node.get('name')
            
            # Check if this is the window we're looking for
            if 'window' in node and node['window'] == window_id:
                return current_workspace, current_output
            
            # Recursively search child nodes
            for child in node.get('nodes', []):
                result = find_window_info(child, current_output, current_workspace)
                if result[0] is not None:  # Found the window
                    return result
            for child in node.get('floating_nodes', []):
                result = find_window_info(child, current_output, current_workspace)
                if result[0] is not None:  # Found the window
                    return result
            
            return None, None
        
        return find_window_info(tree)
    except Exception as e:
        print(f"Error getting window info: {e}")
        return None, None

def find_alacritty_on_monitor(monitor_name):
    """Find Alacritty windows on a specific monitor."""
    try:
        # Get all windows using i3-msg
        output = subprocess.check_output(['i3-msg', '-t', 'get_tree']).decode('utf-8')
        tree = json.loads(output)
        
        def find_windows_on_monitor(node, monitor, windows_list, is_within_monitor=False):
            """Recursively search for Alacritty windows on a specific monitor."""
            # Check if this is an output node
            if node.get('type') == 'output' and node.get('name') == monitor:
                is_within_monitor = True
            elif node.get('type') == 'output' and node.get('name') != monitor:
                is_within_monitor = False
            
            # If we're within the correct monitor and this is a window node
            if is_within_monitor and 'window' in node and node['window'] is not None:
                window_class = node.get('window_properties', {}).get('class', '').lower()
                window_instance = node.get('window_properties', {}).get('instance', '').lower()
                
                # Check if it's Alacritty
                if 'alacritty' in window_class or 'alacritty' in window_instance:
                    windows_list.append({
                        'id': node['window'],
                        'class': window_class,
                        'title': node.get('name', ''),
                        'instance': window_instance,
                        'focused': node.get('focused', False)
                    })
            
            # Recursively search child nodes
            for child in node.get('nodes', []):
                find_windows_on_monitor(child, monitor, windows_list, is_within_monitor)
            for child in node.get('floating_nodes', []):
                find_windows_on_monitor(child, monitor, windows_list, is_within_monitor)
        
        windows = []
        find_windows_on_monitor(tree, monitor_name, windows)
        return windows
        
    except Exception as e:
        print(f"Error finding Alacritty windows: {e}")
        return []

def is_focused_alacritty():
    """Check if the currently focused window is Alacritty."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_tree']).decode('utf-8')
        tree = json.loads(output)
        
        def find_focused_window(node):
            """Find the focused window in the tree."""
            if node.get('focused', False) and 'window' in node:
                return node
            
            for child in node.get('nodes', []):
                result = find_focused_window(child)
                if result:
                    return result
            for child in node.get('floating_nodes', []):
                result = find_focused_window(child)
                if result:
                    return result
            return None
        
        focused = find_focused_window(tree)
        if focused:
            window_class = focused.get('window_properties', {}).get('class', '').lower()
            window_instance = focused.get('window_properties', {}).get('instance', '').lower()
            return 'alacritty' in window_class or 'alacritty' in window_instance
        return False
        
    except Exception as e:
        print(f"Error checking focused window: {e}")
        return False

def find_or_open_terminal():
    """Find and focus Alacritty on current monitor, or open a new one."""
    current_monitor = get_current_monitor()
    if not current_monitor:
        print("Error: Could not determine current monitor")
        sys.exit(1)
    
    print(f"Current monitor: {current_monitor}")
    
    # Check if currently focused window is Alacritty
    if is_focused_alacritty():
        print("Currently focused window is Alacritty, opening new terminal")
        # Open new Alacritty
        try:
            subprocess.Popen(['alacritty'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL, 
                           stdin=subprocess.DEVNULL,
                           start_new_session=True)
            print("Launched new Alacritty terminal")
        except Exception as e:
            print(f"Error launching Alacritty: {e}")
            sys.exit(1)
    else:
        # Find Alacritty windows on current monitor
        alacritty_windows = find_alacritty_on_monitor(current_monitor)
        
        if alacritty_windows:
            # Focus the first Alacritty found
            window = alacritty_windows[0]
            print(f"Found Alacritty on {current_monitor}, focusing it")
            if focus_window_by_id(window['id']):
                print("Focused existing Alacritty terminal")
            else:
                print("Failed to focus Alacritty")
                sys.exit(1)
        else:
            # No Alacritty on current monitor, open new one
            print(f"No Alacritty found on {current_monitor}, opening new terminal")
            try:
                subprocess.Popen(['alacritty'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL, 
                               stdin=subprocess.DEVNULL,
                               start_new_session=True)
                print("Launched new Alacritty terminal")
            except Exception as e:
                print(f"Error launching Alacritty: {e}")
                sys.exit(1)

def find_and_focus_program(program_name, workspace_name, position):
    """Find and focus a program with priority: focused > current workspace > current monitor > any."""
    # First, try to find the program among open windows
    windows = find_window_by_class_or_title(program_name)
    
    if windows:
        # Get current context
        current_workspace = get_current_workspace()
        current_monitor = get_current_monitor()
        
        # Categorize windows by priority
        focused_windows = []
        current_workspace_windows = []
        current_monitor_windows = []
        other_windows = []
        
        for window in windows:
            if window['focused']:
                focused_windows.append(window)
            else:
                workspace, monitor = get_window_workspace_and_monitor(window['id'])
                if workspace == current_workspace:
                    current_workspace_windows.append(window)
                elif monitor == current_monitor:
                    current_monitor_windows.append(window)
                else:
                    other_windows.append(window)
        
        # Choose window based on priority
        if focused_windows:
            chosen_window = focused_windows[0]
            print(f"Found focused {program_name} (already focused)")
        elif current_workspace_windows:
            chosen_window = current_workspace_windows[0]
            print(f"Found {program_name} in current workspace")
        elif current_monitor_windows:
            chosen_window = current_monitor_windows[0]
            print(f"Found {program_name} on current monitor")
        else:
            chosen_window = other_windows[0]
            print(f"Found {program_name} on different monitor")
        
        # Focus the chosen window (no delays)
        print(f"Focusing {program_name} (class: '{chosen_window['class']}', title: '{chosen_window['title']}')")
        if focus_window_by_id(chosen_window['id']):
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

def get_all_workspaces():
    """Get all current workspaces with their names and monitors."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_workspaces']).decode('utf-8')
        workspaces = json.loads(output)
        return [(ws['name'], ws['output']) for ws in workspaces]
    except Exception as e:
        print(f"Error getting workspaces: {e}")
        return []

def get_containers_in_workspace(workspace_name):
    """Get all container IDs in a specific workspace."""
    try:
        output = subprocess.check_output(['i3-msg', '-t', 'get_tree']).decode('utf-8')
        tree = json.loads(output)
        
        def find_containers_in_workspace(node, target_workspace, containers, current_workspace=None):
            """Recursively find containers in the target workspace."""
            # Track current workspace
            if node.get('type') == 'workspace':
                current_workspace = node.get('name')
            
            # If we're in the target workspace and this is a container
            if current_workspace == target_workspace and 'window' in node and node['window'] is not None:
                containers.append(node['window'])
            
            # Recursively search child nodes
            for child in node.get('nodes', []):
                find_containers_in_workspace(child, target_workspace, containers, current_workspace)
            for child in node.get('floating_nodes', []):
                find_containers_in_workspace(child, target_workspace, containers, current_workspace)
        
        containers = []
        find_containers_in_workspace(tree, workspace_name, containers)
        return containers
    except Exception as e:
        print(f"Error getting containers: {e}")
        return []

def move_container_to_workspace_by_id(container_id, target_workspace):
    """Move a container by ID to a target workspace."""
    try:
        result = subprocess.run(['i3-msg', f'[id="{container_id}"]', 'move', 'container', 'to', 'workspace', target_workspace], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error moving container {container_id}: {result.stderr}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error moving container {container_id}: {e}")
        return False

def clear_illegal_workspaces(legal_assignments):
    """Move containers from illegal workspaces to legal ones on the same monitor."""
    # Parse legal workspace assignments
    legal_workspaces = {}  # workspace_name -> position
    legal_by_monitor = {}  # monitor -> [workspace_names]
    
    print("Legal workspaces:")
    for assignment in legal_assignments:
        workspace_name, position = parse_assignment(assignment)
        legal_workspaces[workspace_name] = position
        monitor = get_target_monitor(position)
        if monitor not in legal_by_monitor:
            legal_by_monitor[monitor] = []
        legal_by_monitor[monitor].append(workspace_name)
        print(f"  {workspace_name} -> {position} ({monitor})")
    
    # Get all current workspaces
    all_workspaces = get_all_workspaces()
    illegal_workspaces = [(name, monitor) for name, monitor in all_workspaces if name not in legal_workspaces]
    
    if not illegal_workspaces:
        print("No illegal workspaces found.")
        return
    
    print(f"\nFound {len(illegal_workspaces)} illegal workspaces:")
    for workspace_name, monitor in illegal_workspaces:
        print(f"  {workspace_name} (on {monitor})")
    
    # Process each illegal workspace
    for illegal_workspace, illegal_monitor in illegal_workspaces:
        # Get containers in this illegal workspace
        containers = get_containers_in_workspace(illegal_workspace)
        if not containers:
            print(f"\nWorkspace '{illegal_workspace}' is empty, skipping")
            continue
        
        print(f"\nProcessing workspace '{illegal_workspace}' on {illegal_monitor} with {len(containers)} containers")
        
        # Find a legal workspace on the same monitor
        target_workspaces = legal_by_monitor.get(illegal_monitor, [])
        if not target_workspaces:
            print(f"  No legal workspaces on monitor {illegal_monitor}, trying other monitors...")
            # Fallback: use any legal workspace
            all_legal = list(legal_workspaces.keys())
            if all_legal:
                target_workspace = all_legal[0]
                print(f"  Using fallback workspace: {target_workspace}")
            else:
                print(f"  No legal workspaces available, skipping")
                continue
        else:
            # Use the first legal workspace on the same monitor
            target_workspace = target_workspaces[0]
            print(f"  Moving containers to legal workspace: {target_workspace}")
        
        # Move all containers to the target workspace
        success_count = 0
        for container_id in containers:
            if move_container_to_workspace_by_id(container_id, target_workspace):
                success_count += 1
        
        print(f"  Moved {success_count}/{len(containers)} containers to '{target_workspace}'")

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
    
    # find-or-open-term subcommand
    term_parser = subparsers.add_parser(
        'find-or-open-term',
        help='Find and focus Alacritty terminal on current monitor, or open a new one',
        epilog="Opens a new Alacritty if:\n"
               "  - No Alacritty exists on current monitor\n"
               "  - Currently focused window is already Alacritty\n"
               "Otherwise focuses existing Alacritty on current monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # clear-illegal-workspaces subcommand
    clear_parser = subparsers.add_parser(
        'clear-illegal-workspaces',
        help='Move containers from unlisted workspaces to legal workspaces on the same monitor',
        epilog="Examples:\n"
               "  %(prog)s '2.I=middle' '4.P=right' '1.U=left'\n"
               "  %(prog)s 'Terminal=left' 'Browser=right'\n"
               "Moves containers from any workspace not in this list to a legal workspace on the same monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    clear_parser.add_argument(
        "legal_workspaces",
        nargs='+',
        help="List of legal 'workspace_name=position' pairs. Any workspace not in this list "
             "will have its containers moved to a legal workspace on the same monitor."
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
    elif args.command == 'find-or-open-term':
        # Process find-or-open-term command
        find_or_open_terminal()
    elif args.command == 'clear-illegal-workspaces':
        # Process clear-illegal-workspaces command
        print("Clearing illegal workspaces...")
        clear_illegal_workspaces(args.legal_workspaces)
    else:
        print("No command specified. Use --help to see available commands.")
        sys.exit(1)
