# Map navigation

Phase 5. Makes custom maps easy to navigate with named sections, a route, a minimap, and clear checkpoint order.

## Relevant files

- `maps/<name>/nav/` — nav data per map (sections, route, minimap bounds).
- `tools/mapkit/` — nav validation and route preview export.
- `port/` — in-game minimap and section labels (Phase 5).
- `docs/custom-maps.md` — map format this doc extends.

## Technical details

- Sections: named regions of the track in checkpoint order. Each section has an id, a display name, and a checkpoint range.
- Route: an ordered polyline through the track, used for the minimap and for validating that checkpoints connect.
- Shortcut flags: marks a section as an optional shortcut so the validator can check the route still connects without it.
- Minimap bounds: a 2D rectangle plus transform so the route maps to the minimap image.
- Route preview: mapkit exports an image or JSON for authors to review without running the game.

## Decisions

- Sections are required, not optional. A map with unnamed sections fails validation. Reason: navigation depends on labels.

## Dependencies

- Phase 3 map schema.
- Phase 4 runtime for in-game display.

## Ordered steps

1. Add the nav schema to the manifest (see docs/custom-maps.md).
2. Extend validator rules for section coverage and route connectivity.
3. Implement minimap rendering and section labels in the port.
4. Implement route preview export in mapkit.
5. Playtest the reference map and record notes below.

## Verification

- Validator rejects a map with an unnamed section and a map with a disconnected route.
- A tester finishes the reference map using only the minimap and section labels. Record the playtest here with date and result.

## Status

Not started. Playtest notes: none yet.
