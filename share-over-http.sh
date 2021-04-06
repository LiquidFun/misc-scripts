#!/bin/bash

port=12345

pids=()
killbg() {
    for p in "${pids[@]}"; do
        kill "$p";
    done
}
trap killbg EXIT

if [ $# -ne 0 ]; then
    echo $PWD
    tmpdir=$(mktemp -d "/tmp/share_over_http.XXXXX")
    for file in "$@"; do
        ln -s "$PWD/$file" "$tmpdir/"
    done
    cd $tmpdir
fi

ssh -R $port:localhost:$port $REMOTE_SERVER -N &
pids+=($!)

python -m http.server $port --bind localhost
# pids+=($!)
