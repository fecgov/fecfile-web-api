from rest_framework.routers import DefaultRouter

# Global list to store all routers
_all_routers = []


def register_router(*args, **kwargs):
    router = DefaultRouter(**kwargs)
    _all_routers.append(router)
    return router


def get_all_routers():
    return _all_routers
