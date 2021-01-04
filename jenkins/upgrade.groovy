PYTHON='python3'
PACKAGE_DIR = '/home/jenkins/Downloads/'
WINDOWS = false

ENTERPRISE_PARAM = '--no-enterprise'
if (params['ENTERPRISE']) {
    ENTERPRISE_PARAM = '--enterprise'
}

FORCE_PARAM_OLD = ''
if (params['FORCE_OLD']) {
    FORCE_PARAM_OLD = '--force'
}

FORCE_PARAM_NEW = ''
if (params['FORCE_NEW']) {
    FORCE_PARAM_NEW = '--force'
}

ZIP = ''
if (params['ZIP']) {
    ZIP = '--zip'
}

VERBOSE=''
if (params['VERBOSE']) {
    VERBOSE='--verbose'
}

DISTRO=""
if (pararams['DISTRO'] != "") {
    DISTRO="""-${params['DISTRO']}"""
}
OSVERSION=""
if (pararams['OSVERSION'] != "") {
    OSVERSION="""-${params['OSVERSION']}"""
}
switch (TARGET) {
    case 'windows': 
        PYTHON='python'
        TARGET_HOST=TARGET
        SUDO=''
        TARGET_HOST = """windows${DISTRO}${OSVERSION}"""
        PACKAGE_DIR = 'c:/jenkins/downloads'
        WINDOWS = true
        break

    case 'linux_deb':
        TARGET_HOST="""linux_deb${DISTRO}${OSVERSION}"""
        if (params['ZIP']) {
            SUDO='' // no root needed for zip testing
        } else {
            SUDO='sudo'
        }
        PYTHON='' // Lean on shebang!
        break
    case 'linux_rpm':
        TARGET_HOST="""linux_deb${DISTRO}${OSVERSION}"""
        if (params['ZIP']) {
            SUDO='' // no root needed for zip testing
        } else {
            SUDO='sudo'
        }
        PYTHON='' // Lean on shebang!
        break
    case 'macos':
        TARGET_HOST="""mac${DISTRO}${OSVERSION}"""
        if (params['ZIP']) {
            SUDO='' // no root needed for zip testing
        } else {
            SUDO='sudo'
        }
        PYTHON='' // Lean on shebang!
        break
}

print("""going to work on '${TARGET_HOST}'""")

def runPython(COMMENT, CMD) {
    print(COMMENT)
    print(cmd)
    if (WINDOWS) {
        powershell CMD
    } else {
        sh CMD
    }
}

node(TARGET_HOST)  {
    stage('checkout') {
        checkout([$class: 'GitSCM',
                  branches: [[name: params['GIT_BRANCH']]],
                  extensions: [
                [$class: 'CheckoutOption', timeout: 20],
                [$class: 'CloneOption', timeout: 20]
            ],
                  userRemoteConfigs:
                  [[url: 'https://github.com/arangodb/release-test-automation.git']]])
    }
    stage('fetch old') {
        if (params['VERSION_OLD'] != "") {
            runPython("downloading old package(s) using:",
"""
${PYTHON} ${WORKSPACE}/release_tester/acquire_packages.py ${ENTERPRISE_PARAM} --enterprise-magic ${params['ENTERPRISE_KEY']} --package-dir ${PACKAGE_DIR} ${FORCE_PARAM_OLD} --source ${params['PACKAGE_SOURCE_OLD']} --version "${params['VERSION_OLD']}" --httpuser dothebart --httppassvoid "${params['HTTP_PASSVOID']}" ${ZIP} ${VERBOSE}
""")
        }
    }

    stage('fetch new') {
        runPython("downloading new package(s) using:",
"""
${PYTHON} ${WORKSPACE}/release_tester/acquire_packages.py ${ENTERPRISE_PARAM} --enterprise-magic ${params['ENTERPRISE_KEY']} --package-dir ${PACKAGE_DIR} ${FORCE_PARAM_NEW} --source ${params['PACKAGE_SOURCE_NEW']} --version '${params['VERSION_NEW']}' --httpuser dothebart --httppassvoid '${params['HTTP_PASSVOID']}' ${ZIP} ${VERBOSE}
""")
    }

    stage('cleanup') {
        if (fileExists('/tmp/config.yml')) {
            runPython("cleaning up the system (if):",
"""
${SUDO} ${PYTHON} ${WORKSPACE}/release_tester/cleanup.py ${ZIP}
""")
        } else {
            print("no old install detected; not cleaning up")
        }
    }

    if (params['VERSION_OLD'] != "") {
        stage('upgrade') {
            runPython("Running upgrade test",
"""
${SUDO} ${PYTHON} ${WORKSPACE}/release_tester/upgrade.py ${ENTERPRISE_PARAM} --old-version ${params['VERSION_OLD']} --version ${params['VERSION_NEW']} --package-dir ${PACKAGE_DIR} --publicip 127.0.0.1 ${ZIP} --no-interactive ${VERBOSE} --starter-mode ${params['STARTER_MODE']}
""")
        }
        stage('plain test'){}
    } else {
        stage('upgrade'){}
        stage('plain test') {
            runPython("Running plain install test",
"""
${SUDO} ${PYTHON} ${WORKSPACE}/release_tester/test.py ${ENTERPRISE_PARAM} --version ${params['VERSION_NEW']} --package-dir ${PACKAGE_DIR} --publicip 127.0.0.1 ${ZIP} --no-interactive ${VERBOSE} --starter-mode ${params['STARTER_MODE']}
"""
        }
    }
}
