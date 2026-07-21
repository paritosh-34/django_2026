# CLAUDE.md

## What this project is

A **learning project**, not production software. The goal is understanding Django and DRF —
`restaurant_project` is a sandbox that exists to have something real to try concepts on.

Do not treat shipping concerns as blockers. Auth, rate limiting, secrets hygiene, deployment,
and test coverage are all *worth mentioning once* when relevant, but never gate work on them
and never refactor toward production-readiness unless asked.

## Who I'm working with

Backend developer coming from **Node.js / Express**. Comfortable with backend concepts —
routing, middleware, ORMs, REST, webhooks — but new to Python and Django's conventions.
The gap is almost always *syntax and framework idiom*, not fundamentals.

Their course offered only Spring Boot or Python; they picked Python because they'd rather not
work in Java. So Django is a deliberate choice, but the ecosystem is unfamiliar.

## How to explain things

- **Compare to Node/Express.** "This is Zod, but bidirectional" lands faster than a paragraph
  of Django vocabulary. Reach for the analogy first, then the Django-specific detail.
- **Lead with the mental model, then the syntax.** Knowing *why* class-based views read
  attributes instead of running your function makes the syntax memorable. Syntax alone doesn't stick.
- **Walls of prose don't work for them.** Prefer diagrams, tables, short labelled flows, and
  code with inline comments. If an explanation is running long, that's a signal to draw it instead.
- **Ground examples in this repo.** Use `MenuItem`, `OrderViewSet`, real file paths — not
  `Foo`/`Bar`. Abstract examples force a translation step that costs more than it saves.
- **Point out the trap.** When a pattern has a well-known failure mode (unordered pagination,
  N+1 on a serializer FK, a missing `.as_view()`), say so at the moment it's relevant.

## The field guide

`docs/django-map.html` is a living visual reference — open it in a browser, no server needed.
It has a flow diagram per concept, a filter box, a toggle for Express equivalents, and a
running "gotchas hit so far" table.

**Keep it updated.** When a session teaches something worth remembering, add it there:

- a new concept → a new `<section class="card">` (the nav and filter build themselves from
  the cards' `data-t` and `data-k` attributes — nothing else to edit)
- a bug they hit → a row in the **Gotchas** table
- a topic covered → move it out of **Not learned yet**

Offer to update it at the end of a substantive session rather than waiting to be asked.

## Current state

| App | View style | Notes |
|---|---|---|
| `menu` | HTML function views + DRF `APIView` | Both styles side by side, deliberately, for comparison |
| `orders` | `ModelViewSet` | Straight CRUD. Unpaginated — no `REST_FRAMEWORK` block in settings |
| `payments` | Plain function views | Razorpay links + webhooks. Raw Django on purpose: signature checks and exact status codes |
| `core` | empty | |

`MenuItem` uses a UUID primary key and has no `Meta.ordering` — so anything involving
`LIMIT/OFFSET` needs an explicit `.order_by()`.

## Commands

```bash
python manage.py runserver     # run from restaurant_project/
python manage.py makemigrations
python manage.py migrate
python manage.py check
```

`ALLOWED_HOSTS` has no `testserver` entry, so driving `django.test.Client` from
`manage.py shell` needs it appended at runtime.
