"""Convenience entry point. Run from the repository root."""
import subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'src'/'build_project.py')],check=True)
subprocess.run([sys.executable,str(root/'src'/'make_dashboard.py')],check=True)
print('Analysis, report and dashboard rebuilt.')
