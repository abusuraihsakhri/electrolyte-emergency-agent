#!/usr/bin/env python3
"""
CLI for Electrolyte Emergency Calculator.
Delegates to electrolyte_guard.py for all calculations.
"""
import sys
from electrolyte_guard import main

if __name__ == "__main__":
    sys.exit(main())
