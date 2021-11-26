#!/bin/sh

# remember icon location
script_dir=$(dirname $(realpath $0))
icon="$script_dir/media/lock-icon.png"

# create a temporary directory
tmpdir=$(mktemp -d "/tmp/multi-screen-lock.XXXXX")
cd "$tmpdir"
image="screenshot.png"

# take the screenshot 
scrot "$image"

# pixelate the screenshot
convert "$image" -scale 2% -scale 5000% "$image"

# full multimonitor screenshot size
# current="current 4280 x 1920"
current=$(xrandr | head -n 1 | grep -Po "current \d+ x \d+")

# center x coordinate for whole screenshot
# halfx="2140"
halfx=$(echo "$current" | awk '{print $2/2}')

# center y coordinate for whole screenshot
# halfy="960"
halfy=$(echo "$current" | awk '{print $4/2}')

# x, y, offset_x, offset_y for each monitor:
# monitors_centers="1280 1024 3000 610    1920 1080 1080 493"
monitors_centers=$(xrandr | grep -Po "\d+x\d+\+\d+\+\d+" | sed 's/[x+]/ /g')

# creates for each monitor a translate option to -geometry
# the math looks like this: offset_x + x/2 - halfx (same for y)
# because '-gravity center' centers both images half of the first image size needs to be subtracted
# adjusted="+1500+162 +-100+73"
adjusted=$(echo "$monitors_centers" | awk '{print "+"$3 + $1/2'"-$halfx"' "+" $4 + $2/2'"-$halfy"'}')

# accounts for the fact that '+-' may both be written due to the previous line
# formatted="+1500+162 -100+73"
formatted=$(echo "$adjusted" | sed 's/+-/-/g')

# add the lock-icon for each monitor
for geometry in $formatted; do 
    convert "$image" "$icon" -geometry "$geometry" -gravity center -composite "$image"
done

# finally, lock the screen with the image
i3lock -i "$tmpdir/$image"

# remove temporary directory
rm -r "$tmpdir"


