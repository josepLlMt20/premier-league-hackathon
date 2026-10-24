from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from match_context.domain.contracts import ContextRequest, ContextResult, EvidenceBundle
from match_context.domain.events import MatchMetadata
from .schemas import EvidenceRequest, Health, MatchHead, MatchView, ResolvedCursor

router = APIRouter()
MatchId = Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")]
Cutoff = Annotated[int, Query(ge=0, le=999_999_999_999)]
Second = Annotated[int, Query(ge=0, le=5400)]


@router.get("/healthz", response_model=Health)
async def health():
    """Liveness only: does not assert that storage or model providers are ready."""
    return Health()


@router.get("/api/matches", response_model=tuple[MatchMetadata, ...])
async def matches(request: Request):
    service = request.app.state.context_service
    return await service.read(service.log.list_matches)


@router.get("/api/matches/{match_id}/head", response_model=MatchHead)
async def head(request: Request, match_id: MatchId):
    service = request.app.state.context_service
    position = await service.read(service.log.position, match_id)
    return MatchHead(match_id=match_id, sequence=position.sequence, available_second=position.available_second,
                     ingestion_state=request.app.state.ingestion_states.get(match_id, "external"))


@router.get("/api/matches/{match_id}/cursor", response_model=ResolvedCursor)
async def cursor(request: Request, match_id: MatchId, available_second: Second):
    return await request.app.state.context_service.cursor(match_id, available_second)


@router.get("/api/matches/{match_id}/view", response_model=MatchView)
async def view(request: Request, match_id: MatchId, to_sequence: Cutoff):
    return await request.app.state.context_service.view(match_id, to_sequence)


@router.post("/api/context", response_model=ContextResult)
async def context(request: Request, body: ContextRequest):
    return await request.app.state.context_service.get_context(body)


@router.post("/api/evidence", response_model=EvidenceBundle)
async def evidence(request: Request, body: EvidenceRequest):
    return await request.app.state.context_service.evidence(body)
