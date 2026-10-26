# provek.dev auth.md

## Audience

Any agent or program reading or writing provek.dev.

## Authentication: none

Every resource is public and served to anonymous requests. There is no registration, no API key, no OAuth authorization server, no token endpoint and no /.well-known/oauth-* metadata, because nothing is gated. Do not probe /agent/auth or any registration endpoint: none exists, and the 404 is the answer.

## Readable without credentials

- /data/registry.json
- /data/passports/<slug>.json (CORS-open)
- every page, with `Accept: text/markdown`
- /.well-known/api-catalog
- /.well-known/ai-catalog.json
- /llms.txt
- /.well-known/agent-skills/index.json

## The one write

`POST /api/apply` submits a public repository for verification. It is anonymous. It needs the repository owner's consent, given inside the form, which is why no agent credential exists for it. `GET /api/apply/<id>` reads the state of one request.

## If this changes

This file is the only statement of this site's authentication. A credential, a registration endpoint or OAuth metadata would be announced here first and recorded in DECISIONS.md.

## Security contact

/.well-known/security.txt
