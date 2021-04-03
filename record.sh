#!/bin/bash

# ANSI color codes
# black="BLACK\033[030m"
red="\033[031m"
green="\033[032m"
yellow="\033[033m"
blue="\033[034m"
magenta="\033[035m"
cyan="\033[036m"
white="\033[037m"

Help () {
	echo -e "Printing$magenta Help$white"
	echo -e " - Help\t\t $magenta h $white"
	echo -e " - Record\t $red r $white"
	echo -e " - Exit\t\t $cyan e$white or$cyan q$white or$cyan f$white or$cyan <C-c> $white"
	echo -e " - Play prev\t $yellow p$white"
	echo -e " - Play prev nth $yellow [1-9] $white"
	echo -e " - Delete prev \t $red d$white or$red x$white"
	echo -e " - List rec..ngs $yellow l$white"

	echo ''
}

Help

while true; do
	most_recent_files=$(ls | grep -E '[0-9]+\.wav' | sort -r | head -n 9)         
	curr_file=$(echo "$most_recent_files" | head -n 1)

	printf "$yellow>> $white"

	# Read input
	read -rn1 input

	printf "$yellow -> $white"

	case "$input" in

	# Start and stop recording
	r)
		curr=$(echo "$curr_file" | grep -Eo "[1-9]+0*")
		echo "$curr"
		next=$(printf "%04d.wav" $((curr + 1)))

		echo -e "Recording $cyan$next$blue"
		rec $next
		printf "$white"
	;;

	# Play nth previous song
	p|[1-9])
		if [ "$input" == 'p' ];  then
			input=1
		fi
		nth_file=$(echo "$most_recent_files" | sed "${input}q;d")

		echo -e "Playing $yellow$nth_file$magenta"
		play $nth_file
		printf "$white"
	;;

	# Print help
	h)
		Help
	;;

	# Delete previous track
	d|x)
		# Confirm deletion
		echo -e "Are you sure you want to delete $cyan$curr_file$white? (y/n)"
		read -rsn1 confirm
		if [ $confirm == 'y' ]; then
			echo -e "Deleted $red$curr_file$white"
			rm $curr_file
		else
			echo -e "Cancelled deletion"
		fi
	;;

	# Exit/finish/quit program
	e|f|q)
		echo -e "Exiting$magenta $0"
		break
	;;

	# List recordings
	l)
		echo -e "Listing$yellow recordings"
		ls | grep -E "[0-9]"
	;;

	# Invalid key
	*)
		echo -e "$red! ERROR: $white$input does not seem to be a valid input"
	;;
	esac
done
