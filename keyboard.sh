#!/bin/bash

# Set us layout
setxkbmap us

# Set a more reasonable key-repeat rate
xset r rate 200 50

sleep 1
# Run xmodmap after setting layout (disable caps-lock, add umlauts)
xmodmap ~/.Xmodmap
sleep 1
xmodmap ~/.Xmodmap

# Turn on numlock
# numlockx on
