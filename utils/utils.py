import re

from pathlib import Path
from ida_domain import Database

def detect_kernel_version(db: Database):
    """get the version code from vmlinux"""
    major = 0
    minor = 0
    patchlevel = 0
    addr_list = db.bytes.find_binary_sequence(b"Linux version ")
    pattern = re.compile(r"Linux version (\d+)\.(\d+)\.(\d+)")
    for ea in addr_list:
        banner = db.bytes.get_cstring_at(ea, max_length=0x40)
        if not banner:
            continue
        match = pattern.search(banner)
        if match:
            major, minor, patchlevel = map(int, match.groups())
            break

    return major, minor, patchlevel

def is_newer_kernel(db: Database, dev_type: str):
    """check if have func cdev_init"""
    if dev_type == "char":
        func = db.functions.get_by_name("cdev_init")
        if func is not None:
            return True
        return False
    else:
        raise NotImplementedError
