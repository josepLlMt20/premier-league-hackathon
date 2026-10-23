from match_context.domain.contracts import BoundedSnapshot, EvidenceBundle


def resolve_evidence(snapshot: BoundedSnapshot, ids: tuple[str, ...]) -> EvidenceBundle:
    """Resolve only known events, including their scoring/correction dependencies."""
    known = {event.event_id: event for event in snapshot.known_events}
    selected = set(ids)
    if not selected <= known.keys():
        raise ValueError("Evidence is unavailable at this knowledge cutoff")
    while True:
        previous = selected.copy()
        for event_id in previous:
            event = known[event_id]
            if event.kind == "goal":
                selected.add(event.attributes.shot_event_id)
            elif event.kind == "correction":
                selected.add(event.attributes.target_event_id)
        selected.update(event.event_id for event in snapshot.known_events
                        if event.kind == "correction" and event.attributes.target_event_id in selected)
        if selected == previous:
            break
    return EvidenceBundle(
        snapshot_id=snapshot.snapshot_id, cutoff_sequence=snapshot.cutoff,
        events=tuple(e for e in snapshot.known_events if e.event_id in selected),
        annulled_event_ids=tuple(i for i in snapshot.annulled_event_ids if i in selected),
    )
