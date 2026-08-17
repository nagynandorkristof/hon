import sys
from pathlib import Path

# The pyhon library is vendored under custom_components/hon/pyhon and is
# self-contained (its internal imports are all relative to itself). Importing
# it as `custom_components.hon.pyhon` would execute
# `custom_components/hon/__init__.py`, which requires Home Assistant to be
# installed. Put custom_components/hon on the path so pyhon-only tests can
# `import pyhon` directly without pulling in the HA-dependent integration code.
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "hon"))
