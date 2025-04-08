from rest_framework.routers import DefaultRouter, Route, DynamicRoute, SimpleRouter

class ReadOnlyRouter(SimpleRouter):
    """
    A router for read-only APIs, which doesn't use trailing slashes.
    Note: taken directly from the DRF documentation for Routers.
    """
    routes = [
        Route(
            url=r'^{prefix}$',
            mapping={'get': 'list'},
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        Route(
            url=r'^{prefix}/{lookup}$',
            mapping={'get': 'retrieve'},
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Detail'}
        ),
        DynamicRoute(
            url=r'^{prefix}/{lookup}/{url_path}$',
            name='{basename}-{url_name}',
            detail=True,
            initkwargs={}
        )
    ]


# Global list to store all routers
_all_routers = []


def register_router():
    router = DefaultRouter()
    _all_routers.append(router)
    return router

def register_read_only_router():
    router = ReadOnlyRouter()
    _all_routers.append(router)
    return router

def get_all_routers():
    return _all_routers