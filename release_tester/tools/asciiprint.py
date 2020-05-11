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

def ascii_print(s):
    s = ANSI_ESCAPE.sub('', s)
    print("".join(ch for ch in s if ch == '\n' or unicodedata.category(ch)[0]!="C"))
