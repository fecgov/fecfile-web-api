from .base import *  # NOSONAR # noqa F401, F403

# These settings are for local development only.

try:
    from .local import *  # NOSONAR # noqa F401, F403
except ImportError:
    pass
