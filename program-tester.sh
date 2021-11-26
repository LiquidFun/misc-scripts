#!/usr/bin/bash

# -|-- ------------------------------------------------------------------ --|-
# -|--                           Program Tester                           --|-
# -|-- ------------------------------------------------------------------ --|-

# Takes a filename as input, compiles it if needed, then runs test cases on it.
# These test cases need to be named 1.in, 2.in, 3.in... etc.  The ground truths need to
# be named 1.ans, 2.ans, 3.ans... etc (alternatively .out is accepted as well). 
# It will then show you whether your result matches these ground truths.  
# modify it.  Supports Python, C and C++ right now.

# Additionally implement a quick way to run it with your editor
# I use a vim mapping (add to your .vimrc): 
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
    g++ -std=c++2a -O3 -fsanitize=undefined -Wall -Wextra -Wshadow $1 2>&1 || exit
elif [[ $extension == c ]]; then
    gcc $1
fi
for file in $(\ls | \grep -E \d*.in$); do
    if [[ -e $file ]]; then
        columns=$(tput cols)

        # Print dividing line
        echo -n "──┤$file├"
        for i in $(seq $(($columns - 4 - ${#file}))); do
            echo -n "─"
        done
        echo ""

        # Run with current test
        if [[ "$extension" == cpp ]] || [[ "$extension" == c ]]; then
            runCommand="./a.out"
        elif [[ $extension == py ]]; then
            runCommand="python3 $1"
        fi
        runFile="${file%.in}.run"
        # timeCommand="/usr/bin/time"
        { time $runCommand < $file > $runFile ; } 2>tmp4

        # Check if either .ans or .out file exists
        testFile="${file%.in}.ans"
        if ! [[ -e $testFile ]]; then
            testFile="${file%.in}.out"
        fi
        

        # Depending if there is the results file use it as comparison file
        lineNumberCommand="nl -s ' │ '"
        if [[ -e "$testFile" ]]; then
            eval "$lineNumberCommand" "$testFile" > tmp1
        else
            eval "$lineNumberCommand" "$file" > tmp1
            echo -e "$noAnsFileMsg" >> "tmp1"
        fi
        

        # Show the difference between the two files
        eval "$lineNumberCommand" "$runFile" > tmp2
        # echo -e "$($lineNumberCommand $runFile)" > tmp2
        diff --ignore-trailing-space --report-identical-files --side-by-side --width=$columns --color=always tmp1 tmp2 > tmp3
        lastLine="$(tail -n 1 tmp3)"
        if [[ "$lastLine" == "Files tmp1 and tmp2 are identical" ]]; then
            good=$(($good + 1))
        elif ! [[ -e "$testFile" ]]; then
            unknown=$(($unknown + 1))
        else
            bad=$(($bad + 1))
            different="$different   $file"
        fi
        if ! $summary; then
            cat tmp3
        fi
        cat tmp4 | grep real

        # Calculate totals
        total=$(($total + 1))


        # Delete tmp files
        rm -f tmp1 tmp2 tmp3 tmp4
    fi
done
for i in $(seq $(tput cols)); do
    echo -n "─"
done

echo -e "\nGood: $good/$total; Bad: $bad/$total; Unknown: $unknown/$total"
echo -e "Bad tests:$different"
