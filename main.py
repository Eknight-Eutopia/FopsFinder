from os import path
import sys
import argparse
import subprocess
from pathlib import Path

import ida_domain  # 先完成 IDA 初始化
from ida_domain import Database
from ida_domain.database import IdaCommandOptions


sys.path.insert(0, str(Path(__file__).resolve().parent))

from file_ops import get_char_fops
from block_ops import get_blk_fops
from utils.utils import detect_kernel_version
from utils.logger import get_logger


logger = get_logger("Main Process")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Fops Finder')
    parser.add_argument(
        '-k', '--kernel', help='kernel vmlinux to retrieve fops offsets', type=str, required=True
    )

    args = parser.parse_args()
    kernel_path = Path(args.kernel)

    ida_options = IdaCommandOptions(auto_analysis=True, new_database=False)
    with Database.open(str(kernel_path), ida_options, False) as db:
        major, minor, patchlevel = detect_kernel_version(db)
        logger.info(f"Linux version: {major}.{minor}.{patchlevel}")

        char_fops = get_char_fops(db)
        blk_fops = get_blk_fops(db)


if __name__ == "__main__":
    main()
