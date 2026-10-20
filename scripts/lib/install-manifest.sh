# install-manifest.sh - the JSON manifest of one install run.
#
# This file is a LIBRARY, not a tool: `scripts/install.sh` sources it. It
# holds the machine-readable side of the installer and nothing else, so the
# contract of the manifest lives in one place.
#
# The manifest is the contract `ottili.skills.install-manifest/v1`. Its JSON
# Schema is scripts/ottili_contracts/schemas/ottili.skills.install-manifest.v1.schema.json,
# its typed view scripts/ottili_contracts/models.py and its worked example
# scripts/ottili_contracts/examples/.
#
# The library reads three variables of its caller: MANIFEST_MODE (the mode of
# the run), TARGET (the directory the run is about) and LINK (whether the run
# links instead of copies). It writes MANIFEST_ROWS (one row per skill).
#
# Inputs: the functions below take their arguments as parameters.
# Outputs: manifest_emit prints ONE JSON object on stdout.
# Failure modes: none of the functions exits; manifest_emit prints an empty
#   skill list when no skill was recorded.

# Escape one string for JSON.
#
# Inputs: the raw string.
# Outputs: the escaped string on stdout (without the quotes).
# Failure modes: none.
json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\b'/\\b}"
  s="${s//$'\f'/\\f}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  if [[ "$s" == *[$'\x01'-$'\x1f']* ]]; then
    local out="" ch i
    for ((i = 0; i < ${#s}; i++)); do
      ch="${s:i:1}"
      if [[ "$ch" == [$'\x01'-$'\x1f'] ]]; then
        printf -v ch '\\u%04x' "'$ch"
      fi
      out+="$ch"
    done
    s="$out"
  fi
  printf '%s' "$s"
}

# Print one JSON string literal.
#
# Inputs: the raw string.
# Outputs: the quoted, escaped literal on stdout.
# Failure modes: none.
json_string() {
  printf '"%s"' "$(json_escape "$1")"
}

# Record one skill of the install manifest.
#
# Inputs: name, package, source, destination, action and the optional error.
# Outputs: one row appended to MANIFEST_ROWS; nothing on stdout.
# Failure modes: none.
manifest_add() {
  MANIFEST_ROWS+=("$1|$2|$3|$4|$5|${6-}")
}

# Print the install manifest.
#
# Inputs: the optional error of the run (empty when the run was fine).
# Outputs: one JSON object on stdout, the manifest of contract
#   ottili.skills.install-manifest/v1.
# Failure modes: none. A row without a field is printed as an empty string,
#   which the contract allows.
manifest_emit() {
  local overall_error="${1-}"
  local ok="true" first=1 row name package source destination action error
  [[ -n "$overall_error" ]] && ok="false"
  # A skill that could not be resolved fails the run as well: "ok" is the
  # verdict of the whole run, not of the skills that happened to work.
  for row in "${MANIFEST_ROWS[@]+"${MANIFEST_ROWS[@]}"}"; do
    IFS='|' read -r name package source destination action error <<< "$row"
    [[ "$action" == "error" ]] && ok="false"
  done
  printf '{\n'
  printf '  "contract": "ottili.skills.install-manifest/v1",\n'
  printf '  "mode": %s,\n' "$(json_string "$MANIFEST_MODE")"
  printf '  "target": %s,\n' "$(json_string "$TARGET")"
  printf '  "link": %s,\n' "$([[ $LINK -eq 1 ]] && echo true || echo false)"
  printf '  "ok": %s,\n' "$ok"
  printf '  "skills": ['
  for row in "${MANIFEST_ROWS[@]+"${MANIFEST_ROWS[@]}"}"; do
    IFS='|' read -r name package source destination action error <<< "$row"
    [[ $first -eq 1 ]] || printf ','
    first=0
    printf '\n    {"name": %s, "package": %s, "source": %s, "destination": %s, "action": %s, "error": %s}' \
      "$(json_string "$name")" "$(json_string "$package")" "$(json_string "$source")" \
      "$(json_string "$destination")" "$(json_string "$action")" \
      "$([[ -n "$error" ]] && json_string "$error" || echo null)"
  done
  [[ $first -eq 1 ]] || printf '\n  '
  printf '],\n'
  printf '  "error": %s\n' "$([[ -n "$overall_error" ]] && json_string "$overall_error" || echo null)"
  printf '}\n'
}
