from fastapi.routing import APIRoute

from apps.api.app.main import app


def test_router_response_models() -> None:
    routes = [route for route in app.routes if isinstance(route, APIRoute)]
    missing = [
        route.path
        for route in routes
        if route.response_model is None
        and "DELETE" not in route.methods
        and route.path != "/memory/stream"
    ]
    assert missing == []
