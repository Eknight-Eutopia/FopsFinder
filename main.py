import sys
import argparse
import subprocess
from pathlib import Path

import ida_domain  # 先完成 IDA 初始化

sys.path.insert(0, str(Path(__file__).resolve().parent))

from char.get_fops_def import get_fops
from utils.logger import get_logger

logger = get_logger("Main Process")

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Fops Finder')
    parser.add_argument(
        '-k', '--kernel', help='kernel vmlinux to retrieve fops offsets', type=str, required=True
    )

    args = parser.parse_args()

    fops = get_fops(Path(args.kernel).absolute())

if __name__ == "__main__":
    main()
