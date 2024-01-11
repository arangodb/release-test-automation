echo "Maximum number of memory mappings per process is: `cat /proc/sys/vm/max_map_count`"
echo "Setting maximum number of memory mappings per process to: $((`nproc`*8*8000))"
sudo sysctl -w "vm.max_map_count=$((`nproc`*8*8000))"
echo "Maximum number of memory mappings per process is: `cat /proc/sys/vm/max_map_count`"
