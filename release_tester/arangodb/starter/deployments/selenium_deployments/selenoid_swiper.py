#!/usr/bin/env python3
""" base class for arangodb starter deployment selenium frontend tests """
import os
from pathlib import Path
import re
import shutil


def cleanup_temp_files(is_headless):
    """attempt to cleanup the selenoid docker contaires leftovers"""
    if is_headless and os.getuid() == 0:
        tmpdir = "/tmp"  # tempfile.gettempdir()
        trashme_rx = "(?:% s)" % f"|{tmpdir}/".join(
            [
                "pulse-*",
                "xvfb-run.*",
                ".X99-lock",
                ".X11-unix",
                ".org.chromium.Chromium.*",
                ".com.google.Chrome.*",
                ".org.chromium.Chromium.*",
            ]
        )
        print(f"cleanup headless files: {str(trashme_rx)}")
        for one_tmp_file in Path(tmpdir).iterdir():
            print(f"checking {str(one_tmp_file)}")
            try:
                if re.match(trashme_rx, str(one_tmp_file)) and one_tmp_file.group() == "root":
                    print(f"Purging: {str(one_tmp_file)}")
                    if one_tmp_file.is_dir():
                        shutil.rmtree(one_tmp_file)
                    else:
                        one_tmp_file.unlink()
            except KeyError:
                pass
            except FileNotFoundError:
                pass
