TRAP_CLEANUP+=("${DOCKER} network rm ${DOCKER_NETWORK_NAME}")

trap '
      for TRAP_COMMAND in "${TRAP_CLEANUP[@]}"; do
          echo "+ $TRAP_COMMAND"
          $TRAP_COMMAND
     done;
     ' EXIT
