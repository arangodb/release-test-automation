if [ "$(find "$(pwd)/../" -name "*san*.log*" | wc -l )" -gt 0 ]; then
    tar -cvzf sanlogs.tar.gz "$(pwd)/../"*san*.log*
    printf "\nSan logs found after testrun:\n" >> "$(pwd)/test_dir/testfailures.txt"
    for sanlogfile in $(ls "$(pwd)/../"*san*.log*); do
        printf "${sanlogfile}\n" >> "$(pwd)/test_dir/testfailures.txt"
        cat "${sanlogfile}" >> "$(pwd)/test_dir/testfailures.txt"
    done
    rm -f "$(pwd)/../"*san*.log*
    mv sanlogs.tar.gz "$(pwd)/test_dir/"
    echo "FAILED BY SAN-LOGS FOUND!"
    exit 1
fi
