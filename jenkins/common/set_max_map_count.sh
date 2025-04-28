echo "Maximum number of memory mappings per process is: `cat /proc/sys/vm/max_map_count`"
echo "Setting maximum number of memory mappings per process to: $((`nproc`*8*8000))"
maxcount_val=$((`nproc`*8*8000))
gauge_name="vm.max_map_count"
if test "$(/sbin/sysctl $gauge_name | sed "s;.*= ;;")" -lt "${maxcount_val}"; then
    sudo sysctl -w "${gauge_name}=${maxcount_val}"
fi
echo "Maximum number of memory mappings per process is: $(cat /proc/sys/vm/max_map_count)"
