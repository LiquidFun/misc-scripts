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


# TODO:
# 
# Improve code:
#   * Use tmp files which are guaranteed to not exist instead of tmp{1-4}
#
# New features:
#   * Better color support *e.g. highlight entire test case green when it succeeds)
#   * Print time for worst test case (also show time in red for test cases running longer than 2 s)
# 
# Flags:
#   * Add a flag to only show bad tests
#   * Add some sort of column flag to overwrite the number of columns (e.g. for use in vim command mode)
#   * Add help flag
#
# Bugfixes:
#   * Fix internationalization (use diff return codes)
#   * Fix long lines getting cut off in diff


columns=$(tput cols)
color=false
onlySummary=false
testsPattern="*.in"

# Skip required positional first argument in 'getopts'
OPTIND=2

# Handle flags
while getopts 'scp:' flag; do
    case "${flag}" in
        s) onlySummary=true;;
        c) color=true;;
        p) testsPattern="$OPTARG";;
    esac
done

noAnsFileMsg="No results file! Input instead!"

different=""
unknown=0
good=0
bad=0
total=0


extension="${1##*.}"
name="${1%.*}"
binaryName="$name.bin"

# Compile c++ and c if needed, add set-up runCommand to run each test
case "$extension" in
    cpp)
        g++ -std=c++2a -O3 -fsanitize=undefined -Wall -Wextra -Wshadow -o "$binaryName" "$1" 2>&1 || exit
        runCommand="./$binaryName"
        ;;
    c) 
        gcc "$1" -o "$binaryName"
        runCommand="./$binaryName"
        ;;
    py) 
        runCommand="python3 $1"
        ;;
esac

if [[ -z "$runCommand" ]]; then
    echo "ERROR: Was not able to infer run command from given file $1!"
    exit 1
fi

for file in $testsPattern; do
    if [[ -e "$file" ]]; then

        # Print dividing line
        echo -n "──┤$file├"
        for i in $(seq $(($columns - 4 - ${#file}))); do
            echo -n "─"
        done
        echo ""

        runFile="${file%.in}.run"
        { time "$runCommand" < "$file" > "$runFile" ; } 2>tmp4

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
        diff --ignore-trailing-space --report-identical-files --side-by-side --width=$columns --color=auto tmp1 tmp2 > tmp3
        lastLine="$(tail -n 1 tmp3)"
        if [[ "$lastLine" == "Files tmp1 and tmp2 are identical" ]]; then
            good=$(($good + 1))
        elif ! [[ -e "$testFile" ]]; then
            unknown=$(($unknown + 1))
        else
            bad=$(($bad + 1))
            different="$different   $file"
        fi
        if ! $onlySummary; then
            cat tmp3
        fi
        cat tmp4 | grep real

        # Calculate totals
        total=$(($total + 1))


        # Delete tmp files
        rm -f tmp1 tmp2 tmp3 tmp4
    fi
done
for i in $(seq $columns); do
    echo -n "─"
done

echo -e "\nGood: $good/$total; Bad: $bad/$total; Unknown: $unknown/$total"
echo -e "Bad tests:$different"
