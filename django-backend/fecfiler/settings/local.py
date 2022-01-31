from .base import *  # noqa F403

# These settings are for local development only.

try:
    from .local import *   # noqa F401, F403
except ImportError:
    pass
