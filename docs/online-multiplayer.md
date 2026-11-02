# Online multiplayer

Phase 6. Rooms, lobbies, and networked races with a server-side source of truth. Decisions D2 and D3 are made here.

## Relevant files

- `server/` — planned room service on Cloudflare Workers with Durable Objects (D3).
- `port/net/` — client networking (Phase 6).
- `docs/leaderboards.md` — results feed into leaderboards.

## Technical details

- Room lifecycle: create, join, list, ready, start, leave. Empty rooms expire.
- Race sync: player state sent at a fixed tick. Server validates checkpoint order and finish times.
- Default netcode (D2): server-relayed with authoritative results. Clients send inputs and position, the server checks plausibility (checkpoint order, speed bounds, time bounds).
- Reconnection: a dropped player can rejoin within a timeout; otherwise they are marked DNF.
- GameCube hardware networking needs a Broadband Adapter (UNVERIFIED for this project's target). Dolphin networking is the first test target.

## Decisions

- D2 (open, default): server-relayed, authoritative results.
- D3 (open, default): TypeScript on Cloudflare Workers; Durable Objects hold live room state; D1 holds durable data; Miniflare runs local tests. Hosting is Cloudflare.
- D6 (open): transport on GameCube. A patched DOL has no network layer that matches the BBA. Options: a BBA driver in the DOL, or Dolphin-only BBA emulation. Spike before committing to Phase 6. Cloudflare Workers accept only HTTP and WebSocket traffic from clients, so a console likely cannot reach the Cloudflare server directly (UNVERIFIED; confirm in the spike). Console netcode would need a relay, or the project depends on a native PC port (D1).
- Client input is always untrusted.

## Dependencies

- Phase 4 runtime with a playable race.
- Phase 5 route and checkpoint data.
- Wrangler and Miniflare (server tests), a test client harness.

## Ordered steps

1. Spike the transport (D6) first; the rest of this list waits on it. Then decide D2 and D3 and record them here.
2. Build the room service with its tests.
3. Define the race sync protocol and write it down here.
4. Implement server validation for checkpoints and times.
5. Implement client networking in `port/net/`.
6. Add reconnection and stall handling.
7. Test two clients locally and across a LAN.

## Verification

- Server tests cover room lifecycle, impossible times, and checkpoint skips.
- Two clients finish a race on the reference map. Record the run here with date and setup.

## Status

Not started. D2 and D3 not decided.
