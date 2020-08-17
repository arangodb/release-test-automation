PYTHON='python3'

INSTALL_TARGET = params['INSTALL_TARGET']
ZIP = params['ZIP']


if (INSTALL_TARGET == 'windows_install') {
    PYTHON='python3.exe'
}



node(INSTALL_TARGET)  {




}
