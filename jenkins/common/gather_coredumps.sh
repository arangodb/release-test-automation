if [ `ls -1 $(pwd)/test_dir/core* 2>/dev/null | wc -l ` -gt 0 ]; then
    7z a coredumps $(pwd)/test_dir/core*
    printf "\nCoredumps found after testrun:\n $(ls -l $(pwd)/test_dir/core*)\n" >> $(pwd)/test_dir/testfailures.txt
    rm -f $(pwd)/test_dir/core*
    mv coredumps.7z $(pwd)/test_dir/
    echo "FAILED BY COREDUMP FOUND!"
    exit 1
fi
