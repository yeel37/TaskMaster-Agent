#!/usr/bin/env python3
"""便捷启动"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from taskmaster.cli import main
main()
