if test -n "$FORCE" -o "$TEST_BRANCH" != 'main'; then
    RTA_ARGS+=(--force)
fi

if test -n "$SOURCE"; then
    RTA_ARGS+=(--old-source "$SOURCE" --new-source "$SOURCE")
else
    RTA_ARGS+=(--remote-host 172.17.4.0)
fi
