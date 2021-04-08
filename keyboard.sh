#!/bin/bash

# Set us layout
setxkbmap us

# Set a more reasonable key-repeat rate
xset r rate 200 50

# Run xmodmap after setting layout (disable caps-lock, add umlauts)
xmodmap ~/.Xmodmap

# Turn on numlock
numlockx on
