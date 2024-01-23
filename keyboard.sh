#!/bin/bash

# Reset keys which might get stuck due to barrier issue:
# https://github.com/debauchee/barrier/issues/207#issuecomment-542744072
if [[ "$HOSTNAME" -ne "arrakis" ]]; then
    echo "keyup"
    xdotool keyup Shift_L Shift_R Control_L Control_R Alt_L Alt_R Super_L Super_R Hyper_L Hyper_R Caps_Lock 204 205 206 207
fi

# Set us layout
setxkbmap us

# Set a more reasonable key-repeat rate
xset r rate 200 50

# Run xmodmap after setting layout (disable caps-lock, add umlauts)
# Twice, because it does not work consistently
xmodmap ~/.Xmodmap
# xmodmap ~/.Xmodmap

# Turn on numlock
# numlockx on
