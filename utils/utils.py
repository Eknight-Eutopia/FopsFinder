from ida_domain import Database

def is_newer_kernel(db: Database, dev_type: str):
    """check if have func cdev_init"""
    if dev_type == "char":
        func = db.functions.get_by_name("cdev_init")
        if func is not None:
            return True
        return False
    else:
        raise NotImplementedError
