from starlette.requests import Request


def set_active_connection(request: Request, connection_id: int) -> None:
    request.session["connection_id"] = connection_id


def get_active_connection_id(request: Request) -> int | None:
    return request.session.get("connection_id")


def clear_active_connection(request: Request) -> None:
    request.session.pop("connection_id", None)
