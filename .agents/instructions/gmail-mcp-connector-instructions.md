# Gmail MCP Setup

Two Gmail accounts are configured as separate MCP servers in Claude Code.

| Server name | Gmail account |
|---|---|
| `gmail-enterprise` | `$GMAIL_ENTERPRISE_EMAIL` |
| `gmail-zinc` | `$GMAIL_ZINC_EMAIL` |

Set these in your `.env` file. Credential and token files live in `~/.claude/`. The MCP config is at `~/.claude/mcp.json`.

---

## Files

| File | Purpose |
|---|---|
| `~/.claude/gmail-account1-credentials.json` | GCP OAuth client (project `gmail-mcp-495808`) — used for both accounts |
| `~/.claude/gmail-account1-token.json` | Token for `$GMAIL_ENTERPRISE_EMAIL` |
| `~/.claude/gmail-saini-token.json` | Token for `$GMAIL_ZINC_EMAIL` |
| `gcp-oauth.keys.json` | Source credentials for `gmail-mcp-495808` (do not commit) |
| `gcp-oauth.keys2.json` | Source credentials for `saini-gmail-mcp` (unused for auth, kept for reference) |

---

## GCP Setup (one-time per account)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → project `gmail-mcp-495808`
2. APIs & Services → OAuth consent screen → Test users → add the Gmail address you want to connect
3. The OAuth client credentials are already in `~/.claude/gmail-account1-credentials.json`

---

## Re-authenticating a token (if expired or revoked)

Install the MCP package if not already installed:

```bash
npm install -g @gongrzhe/server-gmail-autoauth-mcp
```

### $GMAIL_ENTERPRISE_EMAIL

```bash
GMAIL_OAUTH_PATH=~/.claude/gmail-account1-credentials.json \
GMAIL_CREDENTIALS_PATH=~/.claude/gmail-account1-token.json \
npx @gongrzhe/server-gmail-autoauth-mcp auth
```

### $GMAIL_ZINC_EMAIL

```bash
GMAIL_OAUTH_PATH=~/.claude/gmail-account1-credentials.json \
GMAIL_CREDENTIALS_PATH=~/.claude/gmail-saini-token.json \
npx @gongrzhe/server-gmail-autoauth-mcp auth
```

Use an incognito window if the browser auto-selects the wrong Google account.

---

## ~/.claude/mcp.json

```json
{
  "mcpServers": {
    "gmail-enterprise": {
      "command": "npx",
      "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"],
      "env": {
        "GMAIL_OAUTH_PATH": "/Users/gsingh/.claude/gmail-account1-credentials.json",
        "GMAIL_CREDENTIALS_PATH": "/Users/gsingh/.claude/gmail-account1-token.json"
      }
    },
    "gmail-zinc": {
      "command": "npx",
      "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"],
      "env": {
        "GMAIL_OAUTH_PATH": "/Users/gsingh/.claude/gmail-account1-credentials.json",
        "GMAIL_CREDENTIALS_PATH": "/Users/gsingh/.claude/gmail-saini-token.json"
      }
    }
  }
}
```

---

## Notes

- Both accounts use the same GCP OAuth client (`gmail-mcp-495808`). The token files are what differentiate the two sessions.
- `GMAIL_CREDENTIALS_PATH` is the env var for the token file — not `GMAIL_TOKEN_PATH` (that doesn't work).
- Any new Gmail account you want to add: add it as a test user in GCP → run the auth command with a new token path → add a new entry in `mcp.json`.
- `gcp-oauth.keys.json` and `gcp-oauth.keys2.json` contain OAuth secrets — add them to `.gitignore` if not already excluded.
