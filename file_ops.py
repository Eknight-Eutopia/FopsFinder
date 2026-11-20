"""
get_fops_def.py
Retrieve struct file_operations's child's offset in kernel
author: eut0pl4
"""
from logging import log

import ida_domain
from ida_domain import Database
from ida_domain.pseudocode import PseudocodeExpressionOp

import ida_ida # this module will be loaded through ida_domain's loading.
from ida_hexrays import cot_idx, cot_obj, cot_ref

from utils.utils import is_newer_kernel
from utils.logger import get_logger

logger = get_logger("CHAR")

tty_magic_funcs = {
    "tty_open": 0,
    "tty_read": 0,
    "tty_write": 0,
    "tty_ioctl": 0
}


def get_byteorder(db: Database):
    """get target database's byteorder"""
    byteorder = "big" if ida_ida.inf_is_be() else "little"
    return byteorder

def validate_tty_fops(db: Database, fops_addr: int):
    """check if target fops is tty_fops"""
    magic_ctr = 0
    for func_name in tty_magic_funcs:
        func = db.functions.get_by_name(func_name)
        if func is None:
            logger.warning(f"{func_name} not found.")
            return False
        tmp_ctr = magic_ctr
        for xref in db.xrefs.to_item(func.start_ea):
            logger.debug(f"xref: {xref.from_ea:#x}, fops: {fops_addr:#x}")
            if xref.from_ea - 0x80 < fops_addr and xref.from_ea > fops_addr:
                magic_ctr += 1
                offset = xref.from_ea - fops_addr
                logger.debug(f"{func_name} xrefs fops, offset is {offset}.")
                tty_magic_funcs[func_name] = offset
                break
        if tmp_ctr == magic_ctr:
            logger.warning(f"{func_name} not xrefs fops.")
    if magic_ctr == 4:
        return True
    return False

def get_tty_fops(db: Database, caller_func_name: str, register_func_name: str):
    """get tty_fops content from caller func"""
    caller_func = db.functions.get_by_name(caller_func_name)
    if caller_func is None:
        logger.warning("caller func not found!")
        return None
    register_func_calls = db.pseudocode.decompile(caller_func).find_calls(register_func_name)
    for call in register_func_calls:
        if call.call_args is None:
            logger.warning("register_func func's args not found.")
            return None
        fops = call.call_args[1]
        fops_base = fops.expression
        if fops_base is None:
            logger.warning("fops arg is None.")
            return None
        if fops_base.op == PseudocodeExpressionOp.OBJ:
            element_size = fops.expression.type_info.get_size()
            if fops_base.obj_ea is None:
                logger.warning(f"fops obj ea is None")
                return None
            fops_addr = db.bytes.get_bytes_at(fops_base.obj_ea, element_size)
            if fops_addr is None:
                logger.warning("fops_addr is None")
                return None
            fops_addr = int.from_bytes(fops_addr, get_byteorder(db))

        elif fops_base.op == PseudocodeExpressionOp.IDX:
            fops_base = fops.expression.x
            if fops_base == None:
                logger.warning("fops idx 0 is None")
                return None
            element_size = fops.expression.type_info.get_size()
            if fops_base.obj_ea is None:
                logger.warning(f"fops obj ea is None")
                return None
            fops_addr = db.bytes.get_bytes_at(fops_base.obj_ea, element_size)
            if fops_addr is None:
                logger.warning("fops_addr is None")
                return None
            fops_addr = int.from_bytes(fops_addr, get_byteorder(db))
        elif fops_base.op == PseudocodeExpressionOp.REF:
            fops_base = fops.expression.x
            if fops_base == None:
                logger.warning("fops idx 0 is None")
                return None
            fops_addr = fops_base.obj_ea if fops_base.obj_ea is not None else 0
        else:
            logger.error(f"Unknown fops type found: {fops_base.op}")
            raise NotImplementedError
        logger.debug(f"fops ea: {fops_base.obj_ea:#x}")

        logger.debug(f"candidate fops: {fops_addr:#x}")
        if validate_tty_fops(db, fops_addr):
            logger.info(f"tty_fops: {fops_addr:#x}")
            return fops_addr



def get_char_fops(db):
    if is_newer_kernel(db, "char"):
        fops_addr = get_tty_fops(db, "tty_init", "cdev_init")
    else:
        fops_addr = get_tty_fops(db, "tty_register_driver", "register_chrdev")

    if fops_addr is not None:
        logger.info(f"file_operations child's offsets:")
        for child in tty_magic_funcs:
            logger.info(f"\t{child}:\t{tty_magic_funcs[child]:#x}")
