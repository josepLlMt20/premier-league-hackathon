from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from match_context.agents.base import AgentRunner
from match_context.config import Settings
from match_context.service.context import ContextService, ServiceError
from match_context.storage.base import EventLog
from .routes import router
from .schemas import ErrorResponse


def create_app(settings: Settings, log: EventLog, runner: AgentRunner | None = None, *, lifespan=None) -> FastAPI:
    """The caller owns storage and runner lifetimes; constructing an app performs no I/O."""
    app = FastAPI(title="Match Context API", version="0.1.0", lifespan=lifespan, responses={
        code: {"model": ErrorResponse, **({"headers": {"Retry-After": {"schema": {"type": "integer"},
                "description": "Seconds before retrying a saturated generation request"}}} if code == 429 else {})}
        for code in (404, 422, 429, 503)})
    app.state.context_service = ContextService(settings, log, runner)
    app.state.ingestion_states = {}

    @app.exception_handler(ServiceError)
    async def service_error(request, error):
        return JSONResponse(status_code=error.status, content={"error": {"code": error.code}},
                            headers={"Retry-After": "1"} if error.status == 429 else None)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        # Do not echo raw bodies, provider strings, validation contexts or secrets.
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_request"}})

    @app.middleware("http")
    async def private_responses(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(router)
    return app
