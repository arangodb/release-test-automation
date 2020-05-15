#!env python
""" removes terminal control sequences and other non ascii characters """
import unicodedata
import re

# 7-bit C1 ANSI sequences
ANSI_ESCAPE = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)

def ascii_print(string):
    """ convert string to only be ascii without control sequences """
    string = ANSI_ESCAPE.sub('', string)
    print("".join(ch for ch in string if ch == '\n' or unicodedata.category(ch)[0] != "C"))
