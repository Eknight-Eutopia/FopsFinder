"""
get_fops_def.py
Retrieve struct block_device_operations's child's offset in kernel
author: eut0pl4
"""

from typing import reveal_type

import ida_domain
from ida_domain import Database

from utils.utils import is_newer_kernel
from utils.logger import get_logger

logger = get_logger("BLK")

SEARCH_RANGE = 0x10
loop_magic_funcs = {
    "lo_open": 0,
    "lo_release": 0,
    "lo_ioctl": 0
}

mtd_magic_funcs = {
    "blktrans_open": 0,
    "blktrans_release": 0,
    "blktrans_ioctl": 0
}


def get_lo_fops(db: Database):
    lo_open_func = db.functions.get_by_name("lo_open")
    if lo_open_func is None:
        logger.warning(f"lo_open not found")
        return None
    lo_open_xrefs = list(db.xrefs.to_item(lo_open_func.start_ea))
    assert len(lo_open_xrefs) == 1
    xref = lo_open_xrefs[0]
    logger.debug(f"lo_open's xref: {xref.from_ea :#x} -> {xref.to_ea :#x}")
    # traverse up to find the actual reference

    fops_ea = xref.from_ea
    for i in range(SEARCH_RANGE):
        fops_xrefs = list(db.xrefs.to_item(fops_ea))
        if len(fops_xrefs) != 0:
            fops_xref = fops_xrefs[0]
            if fops_xref is None or fops_xref.from_ea is None:
                logger.warning("fops_xref is None")
                return None
            logger.debug(f"Possible lo_fops found")
            break
        fops_ea -= 4
    else:
        logger.warning("lo_fops xref not found")
        return None
    
    # validate this address
    loop_add_func = db.functions.get_by_name("loop_add")
    if loop_add_func is None:
        logger.warning(f"loop_add not found")
        return None
    logger.debug(f"fops_xref's ea: {fops_xref.from_ea:#x}")
    logger.debug(f"loop_add_func address range: [{loop_add_func.start_ea:#x}, {loop_add_func.end_ea:#x}]")
    if fops_xref.from_ea > loop_add_func.start_ea and fops_xref.from_ea < loop_add_func.end_ea:
        logger.debug("check pass")
    else:
        logger.warning("fops_xref is not in loop_init")
        return None

    # compute the child's offset
    for funcname in loop_magic_funcs:
        lo_func = db.functions.get_by_name(funcname)
        if lo_func is None:
            logger.warning(f"{funcname} not found")
            continue
        lo_xrefs = list(db.xrefs.to_item(lo_func.start_ea))
        for xref in lo_xrefs:
            if xref.from_ea - fops_ea < 0x80:
                offset = xref.from_ea - fops_ea
                loop_magic_funcs[funcname] = offset
                logger.debug(f"found {funcname}'s offset: {offset :#x}")
    return fops_ea

def get_mtd_fops(db: Database):
    blktrans_open_func = db.functions.get_by_name("blktrans_open")
    if blktrans_open_func is None:
        logger.warning(f"blktrans_open not found")
        return None
    blktrans_open_xrefs = list(db.xrefs.to_item(blktrans_open_func.start_ea))
    assert len(blktrans_open_xrefs) >= 1
    fops_xref = None
    for xref in blktrans_open_xrefs:
        logger.debug(f"blktrans_open's xref: {xref.from_ea :#x} -> {xref.to_ea :#x}")
        # traverse up to find the actual reference

        fops_ea = xref.from_ea
        for i in range(SEARCH_RANGE):
            fops_xrefs = list(db.xrefs.to_item(fops_ea))
            if len(fops_xrefs) != 0:
                fops_xref = fops_xrefs[0]
                if fops_xref is None or fops_xref.from_ea is None:
                    logger.warning("fops_xref is None")
                    return None
                logger.debug(f"Possible mtd_blktrans_ops found")
                break
            fops_ea -= 4
        if fops_xref is not None:
            break
    else:
        logger.warning("mtd_blktrans_ops xref not found")
        return None

    # validate this address
    add_mtd_blktrans_dev_func = db.functions.get_by_name("add_mtd_blktrans_dev")
    if add_mtd_blktrans_dev_func is None:
        logger.warning(f"add_mtd_blktrans_dev not found")
        return None
    logger.debug(f"fops_xref's ea: {fops_xref.from_ea:#x}")
    logger.debug(f"add_mtd_blktrans_dev_func address range: [{add_mtd_blktrans_dev_func.start_ea:#x}, {add_mtd_blktrans_dev_func.end_ea:#x}]")
    if fops_xref.from_ea > add_mtd_blktrans_dev_func.start_ea and fops_xref.from_ea < add_mtd_blktrans_dev_func.end_ea:
        logger.debug("check pass")
    else:
        logger.warning("fops_xref is not in add_mtd_blktrans_dev")
        return None

    # compute the child's offset
    for funcname in mtd_magic_funcs:
        mtd_func = db.functions.get_by_name(funcname)
        if mtd_func is None:
            logger.warning(f"{funcname} not found")
            continue
        mtd_xrefs = list(db.xrefs.to_item(mtd_func.start_ea))
        for xref in mtd_xrefs:
            if xref.from_ea - fops_ea < 0x80:
                offset = xref.from_ea - fops_ea
                mtd_magic_funcs[funcname] = offset
                logger.debug(f"found {funcname}'s offset: {offset :#x}")
    return fops_ea


def get_blk_fops(db):
    if is_newer_kernel(db, "blk"):
        mtd_fops = get_mtd_fops(db)
        logger.info(f"mtd_fops: {mtd_fops:#x}")
        logger.info("block_device_operations child's offsets:")
        for child in mtd_magic_funcs:
            logger.debug(f"\t{child.replace("blktrans_", "")}:\t{mtd_magic_funcs[child]:#x}")
    else:
        logger.info("kernel is too old to have struct block_device_operations")
