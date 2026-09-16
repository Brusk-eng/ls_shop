# First Class Reviews and Ratings — implementation plan

Issue: [bwhtech/commera#82](https://github.com/bwhtech/commera/issues/82)

Three PRs, one per step. Each bullet is one commit-sized task a worker can pick up on its own.

## Settled decisions

- **Verified Purchase** = the shopper owns a `Sales Order` with `docstatus < 2` and
  `order_type = "Shopping Cart"` containing a size Item under this variant. The join is
  `Sales Order Item.item_code → Color Size Item.item_code → Color Size Item.parent → Style Attribute Variant`.
  Keyed on `Sales Order.owner == frappe.session.user`, **never** resolved through `Customer` —
  `core.py:105` mints a new Customer whenever the Contact/Portal-User lookup misses, so one person
  can sit behind several Customer records and a customer-keyed query under-reports.
- **Approve-first moderation.** Reviews are created `is_published = 0` and reach the storefront only
  when the merchant toggles them on.

- **Any signed-in shopper can write a review.** The form is not buyer-gated. The
  `Verified Purchase` badge is what distinguishes a reviewer who actually ordered.

  The issue's goal text says buyer-only, but that collides with decision 1: if only buyers can
  write, every review is verified and the badge is decoration on 100% of rows. Approve-first
  moderation already contains spam, so opening the write is what makes *both* the badge and the
  moderation queue carry information.

## Corrections to the issue's technical notes

- `templates/partials/products_details/product_info.html` does **not** exist. The default theme's
  product detail is a single `body.html`, and there is no `.review-num` div anywhere in the app.
  The star/count line under the title is new markup, not a reuse.
- There is no `commera/doctype/`. DocTypes live in `commera/commera_ecommerce/doctype/`.

---

## Step 1 — Record, gate, endpoints

- **S1-1 · `Product Review` DocType** — create in `commera/commera_ecommerce/doctype/`. Fields:
  `variant` (Link → Style Attribute Variant, reqd), `item_style` (Link → Item, denormalised on save
  for cross-colour rollups), `rating` (Int, 1–5), `review_title` (Data), `comment` (Text),
  `verified_purchase` (Check, read-only), `sales_order` (Link → Sales Order, read-only),
  `purchased_item` (Link → Item, read-only), `is_published` (Check, default 0), `seller_reply` (Text),
  `replied_on` (Datetime), `replied_by` (Link → User). The reviewer is `owner` — no separate user
  field, which would be spoofable and would not match the ownership rule the rest of the app trusts.
  `rating` is an Int and not the `Rating` fieldtype: that stores 0–1 and forces the double star-scale
  conversion the issue warns about. Done when `bench migrate` is clean and a doc creates from console.

  `sales_order` and `purchased_item` store the *evidence* for the badge, not the merchandise: they
  make `verified_purchase` auditable instead of a bare checkbox, and they save the dashboard from
  re-running the purchase join on every detail view (S3-2). Both are set server-side by the resolver
  at create time and are never accepted from the client.

  **Both are frozen at create time.** If the order is later cancelled or returned, the badge does not
  silently flip — approve-first means the merchant already vetted the review, and one quietly losing
  its badge weeks later is worse than a stale one. Same trap as `per_delivered` lying after a return.

  A shopper can buy several sizes of the same variant, but the unique index is `(variant, owner)` —
  one review per product page. So `purchased_item` is resolved deterministically (most recent
  qualifying order line) and is **provenance only**: it is not a claim about which size the review is
  about, and it is not rendered on the storefront. A genuine size-runs-small signal would need the
  review to attach to the size, which is a different data model and out of scope here.
- **S1-2 · Unique index on `(variant, owner)`** — via the DocType's own unique constraint, not a
  patch. Done when a second review by the same user on the same variant raises.
- **S1-3 · Verified-purchase resolver** — `find_qualifying_purchase(variant)` in
  `commera/api/reviews.py`, returning the qualifying `{sales_order, item_code}` row or `None` — not a
  bool, so S1-4 has something to store. A single `frappe.qb` join per the chain above, ordered by
  `Sales Order.creation desc` and limited to 1 so the pick is deterministic when the shopper bought
  several sizes. Done when a seeded order returns a row, a stranger's order returns `None`, and a
  shopper with two qualifying orders always gets the most recent.
- **S1-4 · `submit_review` endpoint** — whitelisted, in `commera/api/reviews.py`. Validates rating
  range and comment length, calls S1-3 and stores `verified_purchase`, `sales_order` and
  `purchased_item` from the row it returns, forces `is_published = 0`, rate-limits per user, throws
  on duplicate. Never `frappe.client.insert` — the
  gate needs somewhere to live.
- **S1-5 · Aggregate fields on `Style Attribute Variant`** — add `average_rating` (Float) and
  `review_count` (Int). Recompute from published reviews only, in the `Product Review` controller on
  publish / unpublish / delete. No scheduled sweep over the catalogue, and not a `Data` field.
- **S1-6 · `get_reviews` read endpoint** — published only, paginated. Returns the rows, the 1–5
  histogram, the average, and `has_reviewed` / `can_review` for the session. Raw timestamps — no
  humanised "2 days ago" string from the server. One query per concern; no N+1 on user names.
- **S1-7 · Tests for S1-3 and S1-5** — real DB, rolled back. Gate: owner match, docstatus,
  order_type, wrong-variant. Aggregate: publish, unpublish, delete, and that unpublished rows never
  count toward the average.

## Step 2 — Storefront *(depends on S1-6)*

- **S2-1 · Controller wiring** — call `get_reviews` in `commera/www/products/details.py`, before
  `context.breadcrumbs`.
- **S2-2 · Shared reviews Jinja macro** — summary (average + count), star histogram, review list with
  the `Verified Purchase` badge, and the seller reply indented beneath the review it answers. One
  macro, both themes consume it. The badge shows the fact of a purchase only — `purchased_item` is
  provenance and is not rendered (see S1-1).
- **S2-3 · Default theme section** — mount S2-2 in
  `commera/templates/partials/products_details/body.html`, after the accordion block and before
  `{% if recommended_items %}`. This file also covers the `www/` fallback.
- **S2-4 · Star line under the product title** — new markup in `body.html`. Hidden entirely when
  `review_count` is 0.
- **S2-5 · summer_theme tab** — a third tab in
  `commera/themes/summer_theme/components/sections/product_tabs.html`, following the existing
  `x-data="{ active_tab: … }"` pattern. Alpine only; Bootstrap's tab JS stays banned.
- **S2-6 · Write-a-review form** — Alpine, posts to `submit_review`, shows a "waiting for approval"
  state on success. Open to any signed-in shopper; a signed-out visitor gets a sign-in prompt
  instead of the form. Not buyer-gated — the badge does the distinguishing.
- **S2-7 · `aggregateRating` in JSON-LD** — into `add_seo()` in `details.py`. Omit the key entirely
  when `review_count` is 0; an empty one is penalised.
- **S2-8 · e2e on both themes** — agent-browser: submit → invisible on the storefront → publish from
  console → visible with the badge.

## Step 3 — Dashboard *(depends on S1-1 … S1-6)*

- **S3-1 · `commera/api/admin/reviews.py`** — `get_reviews(tab, search, start, page_length)` on the
  `commera/api/admin/customers.py` pattern: `has_permission` throw, `PAGE_LENGTH` cap, batched reads
  for product and shopper names.
- **S3-2 · `get_review(name)`** — the detail payload: review, product, shopper, any existing reply,
  and the order link read straight off the stored `sales_order` — never by re-running the S1-3 join.
- **S3-3 · `set_published(name, published)`** — the moderation write; triggers the S1-5 recompute.
- **S3-4 · `save_reply(name, reply)`** — stamps `replied_on` / `replied_by`. Public the moment it saves.
- **S3-5 · Sidebar + route** — `ITEM.reviews` in `dashboard/src/ia/nav.js` under the Storefront group,
  plus `/reviews` and `/reviews/:id` in `dashboard/src/router.js`.
- **S3-6 · `Reviews.vue`** — list on the `Customers.vue` pattern, via `useAdminRead`. Published /
  Unpublished tabs, search, an inline frappe-ui `Switch` with `@click.stop`, and `Rating` with
  **`disabled`** — `readonly` is not a prop and is silently ignored, which is why lms's "read-only"
  averages are still click-editable.
- **S3-7 · `ReviewDetail.vue`** — read-only review, publish toggle, reply composer (frappe-ui has no
  textarea-with-submit, so it is a `Textarea` + `Button`).
- **S3-8 · Empty states** — zero reviews, and zero results in each tab.
- **S3-9 · Full-loop e2e** — write → moderate → publish → reply → reply renders on both storefront
  themes.

## Conventions this work must follow

- Data reaches the dashboard through `useAdminRead` / `useAdminAction` in `dashboard/src/data/api.js`.
  This dashboard does not use `useList` or `createListResource`.
- `frappe.qb` or the ORM only; no raw SQL. No `get_doc` inside a loop.
- Mistakes in the prior art (webshop `Item Review`, lms `LMS Course Review`) not to inherit: an N+1
  `get_value("User", …)` per review, a humanised time string cached server-side, the average stored
  as a `Data` field refreshed by an hourly sweep, star-scale conversion in both client and server,
  and no unique index behind the one-review-per-user rule.

## Branch

Cut a fresh worktree off **`develop`** (not `main` — a worktree off `origin/main` comes up empty).
This plan was written from the `feat/storefront-page-size` worktree, which is locked to issue #9.
