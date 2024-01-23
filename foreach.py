#!/usr/bin/python
import os
import sys
import subprocess

RESET = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[34m"

def foreach(command):
    entries = os.listdir('.')
    for entry in entries:
        if os.path.isdir(entry):
            print(f"{BOLD}{BLUE}### {entry} ###{RESET}")
            os.chdir(entry)
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while executing the command: {e}")
            os.chdir('..')
            print("\n")

def main():
    if len(sys.argv) > 1:
        cmd = ' '.join(sys.argv[1:])
        foreach(cmd)
    else:
        print("Please provide a command to run in each subdirectory.")

if __name__ == "__main__":
    main()
