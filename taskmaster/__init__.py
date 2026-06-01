"""
兼容入口：支持在项目根目录直接运行 `python -m taskmaster.cli`。

实际源码保存在 src/taskmaster，根目录包只负责把模块路径接上。
"""

from pathlib import Path


SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "taskmaster"
__path__.append(str(SRC_PACKAGE))

__version__ = "1.0.0"
