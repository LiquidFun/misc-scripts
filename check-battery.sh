#!/bin/bash
while true; do
    # Write to system log when script is called
    printf 'Battery logging script started' | systemd-cat -t check-battery 
    BATTINFO=`acpi -b`
    if [[ `echo $BATTINFO | grep Discharging` && `echo $BATTINFO | cut -f 5 -d " "` < 01:00:00 ]] ; then
            printf 'condition is true' | systemd-cat -t check-battery #write to log if condition is true
            DISPLAY=:0 /usr/bin/notify-send -u critical "battery" "$BATTINFO"
    fi
    sleep 60
done
