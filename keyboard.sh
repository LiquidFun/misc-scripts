#!/bin/bash

# Set us layout
setxkbmap us

# Run xmodmap after setting layout (disable caps-lock, add umlauts)
xmodmap ~/.Xmodmap

# Turn on numlock
numlockx on
