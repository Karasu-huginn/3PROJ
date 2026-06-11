# Library / Lists Feature — Design

**Date:** 2026-06-11
**Status:** Approved (brainstorming with user)
**Branches:** backend on `fastapi`, frontend on `Antoine`

## Goal

Complete the frontend with the library ("Bibliothèque") features:

- CRUD custom lists from the frontend.
- Three default lists per user — **"À voir/lire"**, **"En cours"**, **"Terminé"** — automatically available for every account and impossible to delete.
- A dashboard showing default lists first, then custom lists.
- Quick-add / quick-remove buttons to/from the default lists on the manga details view.

## Decisions made during brainstorming

| Question | Decision |
|---|---|
| Backend scope | Full backend support. Backend work on the `fastapi` branch, frontend on `Antoine`. |
| Default-list semantics | **Mutually exclusive** — a manga sits in at most one of the three defaults; switching status moves it. |
| Custom list form fields | Name + public/private toggle (default public). Poster derived from the first item's cover, no manual URL field. |
| Quick-add scope on details view | The three status buttons **and** an add/remove checklist for the user's custom lists (customs are non-exclusive). |
| Architecture | "Light shared layer": extract a shared `MangaDetailModal`, add `src/api/collections.ts` fetch helpers, keep the existing tab navigation. No router, no new dependencies. |

## Backend design (`fastapi` branch)

### Model change

`Collections` gains one column:

```python
is_default = Column(Boolean, default=False)
```

⚠️ There is no migration tool — `create_all` does **not** add columns to existing
tables. Applying this requires a one-time manual step on existing databases:

```sql
ALTER TABLE collections ADD COLUMN is_default BOOLEAN DEFAULT FALSE;
```

(or a dev-database reset).

### Default lists — lazy "ensure-on-read"

`GET /collections/me` creates the caller's three default lists (`is_default=True`,
public) if any are missing, then returns the collections. This single mechanism
covers new email registrations, Google OAuth signups, and all pre-existing
accounts — no backfill script, no change to the register flow. Creation is
idempotent: it checks for existing `is_default` rows per user, never duplicates.

Defaults are identified by `is_default`, **never by name** — a user renaming a
custom list to "En cours" breaks nothing.

### Endpoints

All routes use the existing JWT dependency from `auth/` (same
`current_user_dependency` pattern as `auth/router.py`). `user_id` always comes
from the token, never from the request body — `schemas.CollectionsBase` loses
its `user_id` and `poster_url` fields accordingly (the poster is derived, the
owner comes from the token).

The old unauthenticated `GET /collections` (which returns every user's
collections) is **removed**, replaced by `GET /collections/me`.

Route-ordering note: the `/collections/me/...` routes must be declared
**before** the `/collections/{id}/...` routes in the router, otherwise
FastAPI tries to parse `me` as the integer path param and returns 422.

| Endpoint | Behavior |
|---|---|
| `GET /collections/me` | Ensure defaults exist, return the caller's collections — defaults first, then customs by creation date. Each entry: `id`, `name`, `is_default`, `is_public`, `item_count`, `poster_url` (explicit value, else first item's `Media.cover_url`, else `null`). |
| `GET /collections/{id}/items` | Items joined with `Media` → `media_id`, `title` (`title_fr ?? title_en ?? title_original`), `cover_url`. Allowed for the owner, or anyone if the list is public. 404 if absent, 403 otherwise. |
| `POST /collections` | Body `{name, is_public}`. Creates a custom list (`is_default=False`). 409 if the caller already has a list with that name. Fixes the existing duplicate-check that filters on `Users.id` instead of `Collections.user_id`. |
| `PATCH /collections/{id}` | Owner only. Body `{name?, is_public?}`. Renaming a default list → 403; toggling `is_public` is allowed on any list. 409 on duplicate name. Fixes the `filter([...])` crash bug. |
| `DELETE /collections/{id}` | Owner only. **403 if `is_default`** — this is the server-side delete protection. Deletes the list's `CollectionsItems` rows in the same transaction (currently they would be orphaned). |
| `POST /collections/{id}/item/{media_id}` | Existing add-item, now owner-only. 409 if already present. |
| `DELETE /collections/{id}/item/{media_id}` | Existing remove-item, now owner-only. |
| `PUT /collections/me/status/{media_id}` | Body `{collection_id: int \| null}`. The id must reference one of the caller's **default** lists, else 403; `null` clears the status. In one transaction: remove the media from the caller's other default lists, add it to the target. This is the atomic status switch behind the quick buttons. |
| `GET /collections/me/membership/{media_id}` | `{collection_ids: [...]}` — the caller's lists containing this media. Drives button states in the details modal. |

The existing `PATCH /collections/{from_id}/item/{media_id}` (move) stays,
secured owner-only like the rest.

### Error style

The collections router standardizes on real `HTTPException`s (401, 403, 404,
409) instead of the current `{"status": ..., "details": ...}` body-status
dicts. Rationale: every route is being touched for auth anyway, and the
frontend already checks `res.ok` for the auth and media APIs.

### `Media` row availability

Quick-add always happens from the details view, whose fetch upserts the
`Media` row (`media/service.py:39`) — so items can always join `Media` for
title and cover, and no missing-row handling is needed on add.

## Frontend design (`Antoine` branch)

### New files

- **`src/api/collections.ts`** — typed fetch helpers: `fetchMyCollections`,
  `fetchCollectionItems`, `createCollection`, `renameCollection`,
  `setVisibility`, `deleteCollection`, `addItem`, `removeItem`,
  `setMediaStatus`, `fetchMembership`. Plus `Collection` and `CollectionItem`
  interfaces. Each helper reads the JWT from `localStorage`, sets the Bearer
  header, and throws a French-message `Error` on `!res.ok`. On a 401 it clears
  the stale token first (same recovery as the profile page).
- **`src/MangaDetailModal.tsx`** — the details modal extracted as-is from
  `Recherche.tsx` (detail fetch, rating, review form, reviews list) plus the
  new library block (below). Props: `mangaId: string`, `onClose: () => void`.
  It fetches its own data, exactly like `openMangaDetail` does today.
- **`src/Bibliotheque.tsx` + `src/Bibliotheque.css`** — the library tab.

### Changed files

- **`App.tsx`** — the dead "Bibliothèque" nav link becomes a real
  `bibliotheque` tab, same pattern as the existing tabs.
- **`Recherche.tsx`** — slims down to search grid + filters + infinite scroll;
  renders `<MangaDetailModal>` when a card is clicked.

### Dashboard UX (`Bibliotheque.tsx`)

- **Logged out:** message + button switching to the `profil` tab (login page).
- **Logged in:** fetch `/collections/me` on mount. Two sections:
  1. **"Mes statuts"** — the three default lists as cards: poster, name, item
     count. No rename or delete affordances.
  2. **"Mes listes"** — custom lists as cards with a public/private badge,
     rename, and delete (confirm dialog stating items are removed with it).
- **"➕ Nouvelle liste"** button → small form: name + public toggle. 409 →
  inline duplicate-name message.
- **Clicking a card** switches the tab's internal state to a list detail view:
  item grid in the same card style as the search results, each with a
  "Retirer" button, plus back navigation to the dashboard. Clicking an item
  opens the shared `MangaDetailModal`, so quick-add also works from inside the
  library.
- Mutations refetch (`/collections/me` or the items list); controls disable
  while a request is in flight, matching the existing `submittingAction`
  pattern. No global state, no new dependencies.

### Quick-add block (`MangaDetailModal.tsx`)

Rendered only when logged in, between the rating block and the reviews. On
open, two calls set the initial state: `fetchMyCollections()` (the checklist
needs the custom lists' names, and the buttons need the default lists' ids)
and `fetchMembership(mangaId)`.

- **Three segmented status buttons** — À voir/lire · En cours · Terminé. The
  one containing the manga is highlighted. Clicking another calls
  `setMediaStatus(mediaId, targetCollectionId)`; clicking the active one calls
  `setMediaStatus(mediaId, null)` (quick-remove).
- **"Listes personnalisées"** — compact checklist of the user's custom lists;
  toggling calls `addItem` / `removeItem`. Non-exclusive.
- After each action: refetch membership; controls disabled while in flight.
  No optimistic updates.

## Edge cases

- 401 on any collections call → clear token, show "Connecte-toi pour utiliser
  ta bibliothèque".
- Duplicate list name → 409 → inline form message.
- Deleting a non-empty custom list is allowed; its items are deleted with it.
- Renaming a custom list to a default's name is harmless (`is_default` is the
  only marker).

## Branch workflow

Backend first, on a **git worktree** checked out on the `fastapi` branch.
`uvicorn` runs from the worktree while the frontend is developed on `Antoine`
in the main working tree — the frontend codes against the real API and no
mock layer is needed.

## Testing

- **Backend:** add pytest + FastAPI `TestClient` with an in-memory SQLite
  database, covering the collections router: ensure-on-read idempotence,
  default-list rename/delete protection (403), atomic status switch
  (exclusivity), ownership checks, duplicate-name 409.
- **Frontend:** manual verification (`npm run lint`, `tsc -b`, browser
  walkthrough). Introducing a JS test stack is out of scope.

## Out of scope

- React Router / AuthContext / TanStack Query restructuring.
- Reordering items or lists.
- Sharing/browsing other users' public lists (the `is_public` flag is stored
  and toggleable, but no public browsing UI is built here).
- Backfill scripts (ensure-on-read makes them unnecessary).
