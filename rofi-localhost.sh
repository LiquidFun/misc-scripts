#!/bin/bash

# Get listening ports and process names from ss (no network probing needed)
declare -A port_proc
while IFS=$'\t' read -r port proc; do
    [[ -n "$port" ]] && port_proc[$port]="$proc"
done < <(ss -tlnpH 2>/dev/null | awk '
    {
        port = $4; sub(/.*:/, "", port)
        if (port in seen) next
        seen[port] = 1
        proc = "unknown"
        if (index($0, "users:((\"") > 0) {
            proc = $0; sub(/.*users:\(\("/, "", proc); sub(/".*/, "", proc)
        }
        print port "\t" proc
    }')

# Remove well-known non-HTTP ports
for p in 22 53 111 631 3306 5432 5433 6379 11211 27017; do
    unset 'port_proc[$p]'
done

ports=("${!port_proc[@]}")
[[ ${#ports[@]} -eq 0 ]] && notify-send "No Services" "No listening ports" && exit 1

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# Start API checks in background
#   /openapi.json  -> /docs                  (FastAPI)
#   /v3/api-docs   -> /swagger-ui/index.html (Spring Boot)
for port in "${ports[@]}"; do
    ( resp=$(curl -s --connect-timeout 0.1 --max-time 0.2 \
        -w '\n%{http_code}' "http://localhost:$port/openapi.json" 2>/dev/null)
      code="${resp##*$'\n'}"
      if [[ "$code" == "200" ]]; then
          echo "/docs" > "$tmpdir/${port}_endpoint"
          name=$(head -1 <<< "$resp" | grep -oP '"title"\s*:\s*"\K[^"]+' | head -1)
          [[ -n "$name" ]] && echo "$name" > "$tmpdir/${port}_name"
      fi
    ) &
    ( resp=$(curl -s --connect-timeout 0.1 --max-time 0.2 \
        -w '\n%{http_code}' "http://localhost:$port/v3/api-docs" 2>/dev/null)
      code="${resp##*$'\n'}"
      if [[ "$code" == "200" ]]; then
          [[ ! -f "$tmpdir/${port}_endpoint" ]] && \
              echo "/swagger-ui/index.html" > "$tmpdir/${port}_endpoint_sb"
          name=$(head -1 <<< "$resp" | grep -oP '"title"\s*:\s*"\K[^"]+' | head -1)
          [[ -n "$name" ]] && echo "$name" > "$tmpdir/${port}_name_sb"
      fi
    ) &
done

# Brief wait for localhost curls to finish (~20-30ms) — imperceptible
sleep 0.05

# Build column-formatted display lines (bold = has API docs)
lines=()
urls=()
for port in $(printf '%s\n' "${ports[@]}" | sort -n); do
    proc="${port_proc[$port]}"
    endpoint=""
    name=""
    if [[ -f "$tmpdir/${port}_endpoint" ]]; then
        endpoint=$(< "$tmpdir/${port}_endpoint")
        [[ -f "$tmpdir/${port}_name" ]] && name=$(< "$tmpdir/${port}_name")
    elif [[ -f "$tmpdir/${port}_endpoint_sb" ]]; then
        endpoint=$(< "$tmpdir/${port}_endpoint_sb")
        [[ -f "$tmpdir/${port}_name_sb" ]] && name=$(< "$tmpdir/${port}_name_sb")
    fi
    [[ -z "$name" ]] && name="$proc"
    # Escape pango special chars in name
    esc_name="${name//&/&amp;}"
    esc_name="${esc_name//</&lt;}"
    esc_name="${esc_name//>/&gt;}"
    url="localhost:$port${endpoint}"
    row="$(printf '%-45s %-7s %s' "$url" "$port" "$esc_name")"
    if [[ -n "$endpoint" ]]; then
        lines+=("<b>$row</b>")
    else
        lines+=("$row")
    fi
    urls+=("http://localhost:$port${endpoint}")
done

[[ ${#lines[@]} -eq 0 ]] && notify-send "No Services" "No services found" && exit 1

idx=$(printf '%s\n' "${lines[@]}" | rofi -dmenu -i -markup-rows -format i \
    -theme-str 'listview { lines: 25; }' \
    -p "Localhost (${#lines[@]})")

if [[ -n "$idx" && "$idx" =~ ^[0-9]+$ ]]; then
    xdg-open "${urls[$idx]}" &>/dev/null
    i3-msg '[class="firefox"] focus' &>/dev/null
fi &
