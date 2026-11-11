"""Run Ghostline straight from a source checkout (double-click or `pythonw run.pyw`)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from ghostline.app import main  # noqa: E402

raise SystemExit(main())
