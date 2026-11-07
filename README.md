# faceless-studio
## OpsHub

One shared module, `hub.py`, feeds and is triggered by OpsHub in every studio.

**Feed.** `content.episode_ready`, `content.series_state` and
`content.series_finished` are POSTed to `$HUB_URL/ingest` (`schema_version: 1`),
signed with `x-hub-signature-256` using `HUB_WEBHOOK_SECRET`. If the hub only
exposes the older unsigned route, the same event is retried against
`$OPSHUB_URL/emit`, so both hub generations keep working. Emitting is never
fatal: a broken hub cannot kill a render.

**Trigger.** `repository_dispatch` with type `opshub.produce` (or `opshub.run`).
OpsHub sends it with any token that has `contents: write` here. The
`client_payload` supports:

| key | meaning |
|---|---|
| `topic` | free-text brief for the next episode (`new_series` ignores it for a fresh arc) |
| `new_series` | `true` starts a brand-new arc instead of continuing the current one |
| `max_episodes` | override how long the arc runs |
| `reason` | free text, echoed into the run log |

Telegram needs no new bot: the same `TELEGRAM_BOT_TOKEN` works everywhere, only
`TELEGRAM_CHAT_ID` changes per studio.

```bash
curl -X POST https://api.github.com/repos/<owner>/<repo>/dispatches \
  -H "Authorization: Bearer $OPSHUB_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"event_type":"opshub.produce","client_payload":{"topic":"","new_series":false,"reason":"opshub nightly"}}'
```

## Shared image quota

Cloudflare image calls are admitted through OpsHub's signed `/ai-usage/reserve` endpoint. The shared UTC-day limits are 24 calls total and 10 per studio. The ledger counts requests, not Cloudflare neurons, and does not account for other workloads on the same Cloudflare account. If the ledger is missing, unavailable, or at its cap, the studio skips Cloudflare and uses its keyless Pollinations fallback. The existing `HUB_URL` and `HUB_WEBHOOK_SECRET` Actions secrets are required. Deploy the OpsHub PR before merging/enabling this studio change; no new secret is introduced.
