# OAuth 2.1 flow — mcp-2026-07-28

Verified 2026-10-12 against the 2026-07-28 changelog (HTTP 200) and SEP-2575.
The 2026-07-28 revision **deprecates** Dynamic Client Registration (RFC 7591) in
favour of OAuth 2.1 Authorization Code + PKCE with Client ID Metadata Documents.

## The flow (ordered)

1. **Discover.** Call `server/discover`. Read `capabilities.authorization` and the
   `authorizationServers` list. Do not hardcode an issuer.
2. **Resolve the client id.** Fetch the Client ID Metadata Document from the issuer's
   `.well-known/client-id-metadata` (or the path the server named). It declares the
   `client_id`, `redirect_uris`, `scope` and `token_endpoint_auth_method`.
3. **Build the PKCE challenge.** `S256`, 43-128 base64url chars. Store `code_verifier`
   keyed by `(issuer, client_id)` — never in the request, never in logs.
4. **Authorize.** `GET /authorize?response_type=code&client_id=...&redirect_uri=...&scope=...&code_challenge=...&code_challenge_method=S256&state=...`
5. **Validate `iss` before redeeming.** The `state`/`code` is bound to an issuer. If
   the issuer of the token endpoint differs from the one recorded at step 2, reject
   (RFC 9207, enforced by SEP-2468).
6. **Redeem.** `POST /token` with `grant_type=authorization_code`, `code_verifier`,
   `redirect_uri`. Receive `access_token`, `refresh_token`, `expires_in`.
7. **Persist by issuer.** Credentials are keyed by issuer. If the issuer changes,
   re-register — do not reuse the old credentials.
8. **Send.** `Authorization: Bearer <token>` on every request. Refresh before expiry;
   a 401 with `WWW-Authenticate` means the token was rejected — refresh, then retry
   once.

## Thresholds and constants

| Parameter | Value | Source |
|-----------|-------|--------|
| PKCE challenge method | `S256` only; plain is rejected | RFC 7636 §4.2 |
| `code_verifier` length | 43-128 chars | RFC 7636 §4.1 |
| Token refresh skew | refresh 30 s before `expires_in` | convention |
| Issuer mismatch | hard fail, never retry with old creds | SEP-2468 |
| `state` entropy | >= 128 bits | OWASP |

## Decision table

| Situation | Action |
|-----------|--------|
| Server supports Client ID Metadata Documents | Use it. This is the only recommended path |
| Server only supports DCR (RFC 7591) | DCR is **deprecated but kept for backwards compat**; use it and log a deprecation warning |
| `iss` on the token endpoint != recorded issuer | Reject the code; re-run discovery |
| 401 + `WWW-Authenticate` | Refresh token; retry once; if it persists, re-register |
| `redirect_uri` not in the metadata document | Hard fail — the metadata document is the contract |

## Near-miss triggers

- Reusing a `client_id` from issuer A on issuer B -> the AS rejects the code and you
  have no verifier stored under B. Key everything by issuer.
- Sending `client_secret` when the metadata document declared
  `token_endpoint_auth_method: none` -> the AS rejects the request; the document is
  authoritative.
- Caching the token endpoint URL without re-checking `iss` -> a MITM can redirect you.
- Confusing DCR deprecation with "DCR is removed" -> it still works for legacy ASes;
  the failure mode is silent, not an error.

## Worked example

**Good:** client records `(issuer, access_token, refresh_token, expires_at)` in a
store keyed by issuer hash. On issuer change it re-fetches the metadata document,
re-registers, and starts a fresh PKCE flow.

**Bad:** client stores one `client_id` and one token globally. An issuer rotation
silently invalidates the token; the client refreshes against the wrong endpoint and
gets a 401 it cannot interpret.
