# Design

## Source of Truth

`zones` returned by SpringBoot is the source of truth for confirmed areas. A rectangle being drawn remains local until the user selects **Confirm**. After a successful create response, the normalized returned zone is added to the local collection. A failed request keeps the draft so the user can retry.

## API Flow

1. The user drags a rectangle. The frontend stores normalized coordinates in a single draft.
2. Confirm sends `POST /zones` with `stream_id`, generated `zone_name`, `zone_type: phone_forbidden`, normalized coordinates serialized as JSON, and default threshold values.
3. SpringBoot persists the zone and calls AI `POST /config/reload` with `reload_items: [zones]`.
4. The frontend renders every enabled phone-forbidden zone for the active stream.
5. Deleting a selected list item sends `DELETE /zones/{id}`.
6. SpringBoot soft-deletes the zone and reloads AI zone configuration. The frontend removes the zone only after success.

The browser does not call AI directly because SpringBoot already owns reload orchestration and failure logging.

## Multi-zone Matching

A phone event is visible when its target bounding rectangle intersects at least one confirmed phone-forbidden zone for the active stream. With no confirmed zones, phone events remain hidden.

## Interaction

- Confirmed zones receive stable numbered labels.
- A compact overlay list exposes one delete button per zone.
- Selecting delete opens a confirmation prompt naming the affected zone.
- Deletion has an in-progress state and cannot be submitted twice.
- Existing zones remain visible while a new draft is drawn.
- The full-screen monitor provides the same drawing, confirmation, and deletion behavior.
