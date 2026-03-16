# Frontend (Project X)

React 19 + TypeScript + Vite 7 app connecting to the OpenClaw personal AI gateway.

## Scripts

| Command        | Description           |
|----------------|-----------------------|
| `pnpm dev`     | Start dev server      |
| `pnpm build`   | Type-check + build    |
| `pnpm preview` | Preview production    |
| `pnpm lint`    | Run ESLint            |
| `pnpm test`    | Run Vitest            |

## Stack

- React 19, Vite 7, TypeScript
- Zustand (state), Lucide React (icons)
- WebSocket transport to OpenClaw gateway (Ed25519 device auth)

## Integrations

The **Integration Hub** (`src/ui/tools/integrations/`) supports connecting external services via API key or OAuth 2.0 popup flow.

### Supported OAuth providers

| Category          | Integrations                                                 |
|-------------------|--------------------------------------------------------------|
| Google Workspace  | Meet, Docs, Sheets, Slides, Drive                            |
| Microsoft         | Teams, Outlook, Calendar                                     |
| Communication     | Slack                                                        |
| Productivity      | Notion, LinkedIn                                             |

OAuth uses a PKCE popup flow where supported. Notion uses HTTP Basic auth for token exchange (as required by the Notion API). Slack uses the OAuth v2 authorization flow.

### LLM Providers

| Provider      | Auth   | Notes                                      |
|---------------|--------|--------------------------------------------|
| OpenAI        | API key | GPT-4.1, o1, o3, o4 series               |
| Anthropic     | API key | Claude Opus/Sonnet/Haiku                  |
| Google AI     | API key | Gemini 2.5 / 3 preview                   |
| Groq          | API key | Ultra-fast LLaMA / Mixtral inference      |
| Mistral       | API key | Mistral Large, Small, Codestral           |
| Grok (xAI)    | API key | Grok 3, Grok 2                            |
| Perplexity    | API key | Sonar Pro / Sonar Reasoning               |
| Cohere        | API key | Command A / Command R+                    |
| Together AI   | API key | Open-source hosted models                 |

Active LLM providers (API key set + enabled) display an **Active** badge in the hub.

### Web Search

Brave Search, Perplexity Search, SerpAPI, Serper, Google Custom Search, Bing Search, DuckDuckGo, Tavily.

## Architecture

See [../README.md](../README.md) for repo overview and OpenClaw.
See [`ARCHITECTURE.md`](ARCHITECTURE.md) for full frontend architecture and data flow.
See [`OPENCLAW_INTEGRATION_SPEC.md`](OPENCLAW_INTEGRATION_SPEC.md) for the WebSocket protocol contract.
