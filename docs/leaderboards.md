# Leaderboards

Phase 7. Per-map leaderboards with authenticated, validated run submissions.

## Relevant files

- `server/` — endpoints, schema, and validation (shared with Phase 6).
- `server/migrations/` — planned schema migrations.
- `port/` — in-game submission and leaderboard screen.

## Technical details

- Entities: maps, players, runs, best times per map and mode.
- Submission: the client sends a run with its checkpoint splits and final time. The server checks checkpoint order, time bounds per section, and duplicate run IDs.
- Storage: store only the best run per player per map and mode, plus a rejected-run log with reasons.
- Reads: top N, a player's rank, and paging.
- Ties: broken deterministically by earliest submission time, then run ID.
- Identity (D5, open, default): anonymous player IDs with a display name. Account system deferred.

## Decisions

- D5 (open, default): anonymous IDs with display names.
- Only server-validated runs are ranked. Client-reported times alone are never accepted.
- Plausibility checks reject impossible runs but cannot prove a run is honest. With anonymous identity (D5), a cheater with a plausible run can still reach the board. Accept this, or revisit D5.

## Dependencies

- Phase 6 server and race results.
- A database for the server: Cloudflare D1 (SQLite), tested locally with Miniflare (D3).

## Ordered steps

1. Decide D5 and record it here.
2. Define the schema and migrations.
3. Implement the submission endpoint with validation and rejection logging.
4. Implement read endpoints: top N, rank, paging.
5. Add in-game submission after a finished race.
6. Add the leaderboard screen to the port.

## Verification

- Server tests: valid run ranks; implausible, out-of-order, and duplicate submissions are rejected with a logged reason.
- Ties return the same order on repeated reads.

## Status

Not started. D5 not decided.
