#!/usr/bin/env python3
""" return formated timestamp"""
import datetime


def timestamp():
    """get the formated "now" timestamp"""
    return datetime.datetime.utcnow().isoformat()
