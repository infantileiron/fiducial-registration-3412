import os, sys, tempfile, importlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DATABASE_URL', 'sqlite:////tmp/fiducial-tests.sqlite')
os.environ.setdefault('ARTIFACT_DIR', '/tmp/fiducial-test-artifacts')
os.environ.setdefault('TASK_MODE', 'inline')
os.environ.setdefault('SEED_DEMO', 'false')
