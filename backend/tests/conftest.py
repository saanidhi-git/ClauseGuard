"""Use a throwaway database for tests (set before the app is imported)."""

import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
