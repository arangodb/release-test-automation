ssh -o StrictHostKeyChecking=no -T git@github.com
if test ! -d "$(pwd)/release_tester/tools/external_helpers"; then
    git clone git@github.com:arangodb/release-test-automation-helpers.git
    mv "$(pwd)/release-test-automation-helpers" "$(pwd)/release_tester/tools/external_helpers"
fi
git submodule init && git submodule update || exit 1
