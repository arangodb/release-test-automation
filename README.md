


Dependencies
------------
- Python expect - https://github.com/pexpect/pexpect https://pexpect.readthedocs.io/en/stable/ (debian only)
- PS-util  https://psutil.readthedocs.io/en/latest/#windows-services on windows `_pswindows.py` needs to be copied 
 into the python installation after the pip run: 
   - python install root (i.e. Users/willi/AppData/Local/Programs/Python)
   -  /Python38-32/Lib/site-packages/psutil/_pswindows.py
 the upstream distribution doesn't enable the wrappers to start/stop service 
- pyyaml - for parsing saved data.


GOAL
====
create most of the flow of i.e. https://github.com/arangodb/release-qa/issues/264 in a portable way. 


Structure going to become:
https://docs.python-guide.org/writing/structure/


attic_snippets/ contains examples and development test code 
