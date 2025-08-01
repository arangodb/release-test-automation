if test -n "$FORCE" -o "$TEST_BRANCH" != 'main'; then
    RTA_ARGS+=(--force)
fi

if test -n "$SOURCE"; then
    if test -z "$UPGRADE_MATRIX"; then
        RTA_ARGS+=(--old-source "$SOURCE" --new-source "$SOURCE")
    else
        RTA_ARGS+=(--source "$SOURCE" --other-source "$SOURCE")
    fi
else
    if test -n "$OLD_SOURCE$NEW_SOURCE"; then
        RTA_ARGS+=(--old-source "$OLD_SOURCE" --new-source "$NEW_SOURCE")
    else
        RTA_ARGS+=(--remote-host 172.17.4.0)
    fi
fi
