#!/usr/bin/env python3
# Copyright - 2019 - Jan Christoph Uhde <Jan@UhdeJC.com>

from .logging_helper import obi_logging_logger as logger
import sys, os
from pathlib import Path

def remove_from_front(path:Path, *args):
    parts = list(path.parts)
    for arg in args:
        if parts[0] == arg:
            parts = parts[1:]
        else:
            return path
    return Path().joinpath(*parts)

def change_ext(path:Path, ext):
    return Path(path.parent).joinpath(path.stem + ext)

def apply_action_to_files(path, action, *filters):
    for root, dirs, files in os.walk(path.resolve()):
        for filename in files:
            file_path=Path(root, filename)

            allow = True
            for filter in filters:
                if not (filter(file_path)):
                    allow = False
                    break

            if allow:
                action(file_path.resolve())

def create_filter_path(*paths):
    def filter_path(path: Path):
        absolute_path = path.resolve()
        for prefix in paths:
            absolute_prefix_path = Path(prefix).resolve()
            if str(absolute_path).startswith(str(absolute_prefix_path)):
                logger.debug(str(absolute_path))
                return True
        return False
    return filter_path

def filter_cpp(path):
    if path.suffix in [ ".cpp", ".cc", ".c", ".hpp", ".h" ]:
        return True
    else:
        return False
