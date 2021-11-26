#!/bin/bash

# -|-- ------------------------------------------------------------------ --|-
# -|--                           Program Tester                           --|-
# -|-- ------------------------------------------------------------------ --|-

# Takes a filename as input, compiles it if needed, then runs test cases on it.
# These test cases need to be named A, B, C... etc.  The ground truths need to
# be named A1, B1, C1... etc. It will then show you whether your result 
# matches these ground truths.  No file extensions! Although feel free to
# modify it.  Supports Python, C and C++ right now.

# Additionally implement a quick way to run it with your editor/desktop
# environment. I use a vim mapping: 
# nnoremap <CR> :w<CR>:!/absolute/file/location/program-tester.sh %<CR>

color=false
summary=false

# Skip required positional first argument
OPTIND=2

while getopts 'sc' flag; do
    case "${flag}" in
        s) summary=true;;
        c) color=true;;
    esac
done

noAnsFileMsg="No results file! Input instead!"

different=""
unknown=0
good=0
bad=0
total=0

# Compile c++ and c if needed
extension=${1##*.}
if [[ $extension == cpp ]]; then
    g++ -std=c++2a -O3 -fsanitize=undefined -Wall -Wextra -Wshadow $1 || exit
elif [[ $extension == c ]]; then
    gcc $1
fi
for file in $(\ls | \grep -E \d*.in$); do
    if [[ -e $file ]]; then
        # Print dividing line
        echo -n "────┤"
        echo -n "$file├"
        for i in $(seq $(($(tput cols) - 6 - ${#file}))); do
            echo -n "─"
        done
        echo ""

        # Run with current test
        if [[ "$extension" == cpp ]] || [[ "$extension" == c ]]; then
            runCommand="./a.out"
        elif [[ $extension == py ]]; then
            runCommand="python3 $1"
        fi
        runFile=${file%.in}.run
        # timeCommand="/usr/bin/time"
        { time $runCommand < $file > $runFile ; } 2>tmp4

        # Check if either .ans or .out file exists
        testFile=${file%.in}.ans
        if ! [[ -e $testFile ]]; then
            testFile=${file%.in}.out
        fi

        # Depending if there is the results file use it as comparison file
        if [[ -e $testFile ]]; then
            echo -e "$(nl $testFile)" > "tmp1"
        else
            cat "${file}" > "tmp1"
            echo -e "$noAnsFileMsg" >> "tmp1"
        fi

        # Show the difference between the two files
        echo -e "$(nl $runFile)" > "tmp2"
        if $color; then
            diffComand=colordiff
        else
            diffCommand=diff
        fi
        $diffCommand --ignore-trailing-space --report-identical-files --side-by-side tmp1 tmp2 > tmp3
        lastLine="$(tail -n 1 tmp3)"
        if [[ "$lastLine" == "Files tmp1 and tmp2 are identical" ]]; then
            good=$(($good + 1))
        elif [[ "$lastLine" == "$noAnsFileMsg" ]]; then
            unknown=$(($unknown + 1))
        else
            bad=$(($bad + 1))
            different="$different;   $file"
        fi
        if ! $summary; then
            cat tmp3
        fi
        cat tmp4

        # Calculate totals
        total=$(($total + 1))


        # Delete tmp files
        if [[ -e tmp1 ]]; then
            rm tmp1
        fi
        if [[ -e tmp2 ]]; then
            rm tmp2
        fi
        if [[ -e tmp3 ]]; then
            rm tmp3
        fi
        if [[ -e tmp4 ]]; then
            rm tmp4
        fi
    fi
done
for i in $(seq $(tput cols)); do
    echo -n "─"
done

echo -e "Good: $good/$total; Bad: $bad/$total; Unknown: $unknown/$total"
echo -e "Bad tests:$different"
