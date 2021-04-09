#!/bin/sh

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

# Compile c++ and c if needed
extension=${1##*.}
if [[ $extension == cpp ]]; then
    g++ -std=c++17 -fsanitize=undefined -Wall -Wextra -Wshadow $1 || exit
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
        runFile=$(echo $file | \sed "s/.in/.run/g")
        if [[ $extension == cpp ]]; then
            echo -e "$(./a.out < $file)" > $runFile
        elif [[ $extension == c ]]; then
            echo -e "$(./a.out < $file)" > $runFile
        elif [[ $extension == py ]]; then
            echo -e "$(python3 $1 < $file)" > $runFile
        fi

        # Depending if there is the results file use it as comparison file
        testFile=$(echo $file | \sed "s/.in/.out/g")
        if [[ -e $testFile ]]; then
            echo -e "$(nl $testFile)" > "tmp1"
        else
            echo -e "No results file! Input instead:" > "tmp1"
            cat "${file}" >> "tmp1"
        fi

        # Show the difference between the two files
        echo -e "$(nl $runFile)" > "tmp2"
        if [[ $2 == "--color" ]]; then
            colordiff --report-identical-files --side-by-side tmp1 tmp2
        else
            diff --report-identical-files --side-by-side tmp1 tmp2
        fi
        echo -e $output

        # Delete tmp files
        if [[ -e tmp1 ]]; then
            rm tmp1
        fi
        if [[ -e tmp2 ]]; then
            rm tmp2
        fi
    fi
done
for i in $(seq $(tput cols)); do
    echo -n "─"
done
