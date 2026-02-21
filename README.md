# ClawSwarm

![Banner image](images/bg.png)

<p align="center">
  <a href="https://pypi.org/project/claw-swarm/" target="_blank">
    <picture>
      <source srcset="https://img.shields.io/pypi/v/swarms?style=for-the-badge&color=3670A0" media="(prefers-color-scheme: dark)">
      <img alt="Version" src="https://img.shields.io/pypi/v/claw-swarm?style=for-the-badge&color=3670A0">
    </picture>
  </a>
  <a href="https://pypi.org/project/claw-swarm/" target="_blank">
    <picture>
      <source srcset="https://img.shields.io/pypi/dm/swarms?style=for-the-badge&color=3670A0" media="(prefers-color-scheme: dark)">
      <img alt="Downloads" src="https://img.shields.io/pypi/dm/claw-swarm?style=for-the-badge&color=3670A0">
    </picture>
  </a>
  <a href="https://twitter.com/swarms_corp/">
    <picture>
      <source srcset="https://img.shields.io/badge/Twitter-Follow-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" media="(prefers-color-scheme: dark)">
      <img src="https://img.shields.io/badge/Twitter-Follow-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter">
    </picture>
  </a>
  <a href="https://discord.gg/EamjgSaEQf">
    <picture>
      <source srcset="https://img.shields.io/badge/Discord-Join-5865F2?style=for-the-badge&logo=discord&logoColor=white" media="(prefers-color-scheme: dark)">
      <img src="https://img.shields.io/badge/Discord-Join-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord">
    </picture>
  </a>
</p>


**A smaller, lighter-weight version of [OpenClaw](https://github.com/openclaw/openclaw)**—natively multi-agent, compiles to Rust, and built on the **[Swarms](https://github.com/kyegomez/swarms) framework** and Swarms ecosystem. One API, unified messaging across Telegram, Discord, and WhatsApp with optional Claude-powered reasoning. Production-ready: gRPC gateway, prompts in code (`claw_swarm.prompts`), and 24/7 operation. Dockerfile included (Python 3.12).

---

## Overview

ClawSwarm is a streamlined, multi-agent alternative to OpenClaw. It delivers **natively multi-agent** AI that responds to users on Telegram, Discord, and WhatsApp through a centralized **Messaging Gateway**. The gateway normalizes incoming messages; the **ClawSwarm Agent** (Swarms framework, configurable system prompt, Claude as a tool) processes each message and replies via a **Replier** back to the originating channel. Built on the Swarms ecosystem for reliability, security, and minimal operational overhead—with a path to **compile to Rust** for performance and deployment flexibility.

**Key capabilities**

- **Lighter than OpenClaw** — Smaller footprint and simpler stack; same multi-channel vision without the full OpenClaw surface area.

- **Natively multi-agent** — Designed from the ground up for multi-agent orchestration on the Swarms framework and Swarms ecosystem.

- **Unified ingestion** — One gRPC API for all supported channels; add or remove platforms without changing agent logic.

- **Swarms-native agent** — Industry-standard orchestration, configurable model and system prompt, Claude available as a tool for deep reasoning and code.

- **Compiles to Rust** — Build path to Rust for performance and deployment flexibility.

- **Prompts in code** — Agent and Claude-tool prompts are Python strings in `claw_swarm.prompts`; override via `create_agent(system_prompt=...)` or edit the module.

- **Production-ready** — Optional TLS, environment-based configuration, long-running agent loop suitable for systemd, Docker, or managed runtimes.

---

## Architecture

### End-to-end flow

Messages travel in a single pipeline: **messaging apps** → **gRPC gateway** → **hierarchical swarm** → **summarizer** → **replier** → back to the **messaging app**. The agent process polls the gateway, runs the swarm on each message, then sends the reply via the replier (Telegram/Discord/WhatsApp APIs). No platform-specific logic lives in the swarm—only a unified `UnifiedMessage` and `Platform` for routing replies.

```mermaid
flowchart LR
    subgraph apps["Messaging apps"]
        TG[Telegram]
        DC[Discord]
        WA[WhatsApp]
    end
    subgraph gw["gRPC gateway"]
        ADAPT[Adapters]
        GRPC[PollMessages / StreamMessages]
        ADAPT --> GRPC
    end
    subgraph swarm["Hierarchical swarm"]
        DIR[Director ClawSwarm]
        R[Response]
        S[Search]
        T[TokenLaunch]
        D[Developer]
        DIR --> R
        DIR --> S
        DIR --> T
        DIR --> D
    end
    SUM[Summarizer]
    RPL[Replier]
    apps -->|fetch & normalize| gw
    gw -->|UnifiedMessage| swarm
    R --> SUM
    S --> SUM
    T --> SUM
    D --> SUM
    SUM --> RPL
    RPL -->|Telegram / Discord / WhatsApp APIs| apps
```

---

### Messaging apps and gRPC gateway

| Layer | Role |
|-------|------|
| **Messaging apps** | Telegram, Discord, and WhatsApp. Users send messages in their app; replies appear in the same chat/channel/thread. |
| **Gateway** | Single gRPC server that **ingests** from all platforms. Each platform has an adapter (e.g. `TelegramAdapter`, `DiscordAdapter`, `WhatsAppAdapter`) that fetches new messages and normalizes them to a **UnifiedMessage** (id, platform, channel_id, thread_id, sender, text, attachments, timestamp). The gateway exposes **PollMessages** (agent polls for new messages) and **StreamMessages** (server-streaming). Optional TLS via `GATEWAY_TLS` and cert/key files. |

So: **Messaging apps** → platform APIs (Telegram Bot API, Discord API, WhatsApp Cloud API) → **gateway adapters** → **gRPC gateway** → one unified stream of `UnifiedMessage`s for the agent.

---

### Hierarchical swarm (agent architecture)

The brain of ClawSwarm is a **hierarchical swarm** (Swarms `HierarchicalSwarm`): one **director** agent and several **worker** agents. The director does not answer users directly; it **plans and delegates** by outputting **SwarmSpec** (plan/orders) that the framework parses and executes.

- **Director (ClawSwarm)**  
  - Single “boss” agent: ClawSwarm identity + hierarchical director instructions.  
  - Receives the user message (with system prompt and optional memory).  
  - Outputs **SwarmSpec** (which worker to call and with what task).  
  - No tools; its job is routing and task decomposition.

- **Workers (specialist agents)**  
  - **ClawSwarm-Response** — Greetings, short Q&A, clarifications. No tools.  
  - **ClawSwarm-Search** — Web/semantic search via `exa_search`.  
  - **ClawSwarm-TokenLaunch** — Launch tokens and claim fees (Swarms World): `launch_token`, `claim_fees`.  
  - **ClawSwarm-Developer** — Code and reasoning via Claude Code: `run_claude_developer` (Read, Write, Edit, Bash, etc.).  

Worker results are aggregated by the swarm; the **director** can request multiple workers in one plan. So the **hierarchy** is: **Director** → **Workers** → combined output.

| Agent | Role | Tools |
|-------|------|-------|
| **ClawSwarm** (Director) | Plan and assign tasks via SwarmSpec; no direct reply. | — |
| **ClawSwarm-Response** | Simple replies, greetings, general Q&A. | None |
| **ClawSwarm-Search** | Web/semantic search. | `exa_search` |
| **ClawSwarm-TokenLaunch** | Launch tokens, claim fees (Swarms World). | `launch_token`, `claim_fees` |
| **ClawSwarm-Developer** | Code, refactor, debug via Claude Code. | `run_claude_developer` |
| **ClawSwarm-TelegramSummarizer** | Shorten swarm output for chat; no emojis. | None |

---

### Response back to the messaging app

After the hierarchical swarm returns:

1. **Summarizer** — Raw swarm output is passed to **ClawSwarm-TelegramSummarizer** to produce a short, chat-friendly reply (no emojis). If summarization is empty, the runner falls back to extracting the final agent reply from the raw output.
2. **Replier** — The agent runner calls **Replier** (`send_message_async`) with the same `platform`, `channel_id`, and `thread_id` as the original `UnifiedMessage`. The replier uses the **same platform credentials** as the gateway (e.g. `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `WHATSAPP_ACCESS_TOKEN`) and sends the text via the **Telegram Bot API**, **Discord API**, or **WhatsApp Cloud API** so the reply appears in the user’s chat.

So the **response path** is: **Swarm output** → **Summarizer** → **Replier** → **Platform API** → **Messaging app** (Telegram/Discord/WhatsApp).

### Relationship to OpenClaw

[OpenClaw](https://github.com/openclaw/openclaw) is a full-featured personal AI assistant (gateway, many channels, voice, canvas, nodes, skills). **ClawSwarm** is a smaller, lighter-weight take on that vision: natively multi-agent, built on the Swarms framework and Swarms ecosystem, with a path to compile to Rust. Use ClawSwarm when you want a lean, multi-agent messaging layer; use OpenClaw when you need the full product (companion apps, voice, canvas, etc.).

---

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt` (no version pins; use a venv and pin locally if needed)
- [Swarms](https://github.com/kyegomez/swarms) framework and Swarms ecosystem; [Claude Code](https://docs.anthropic.com/en/docs/build-with-claude/claude-code) (for the Claude tool)
- Platform credentials for the channels you enable: Telegram Bot Token, Discord Bot Token and Channel IDs, and/or WhatsApp Cloud API credentials

---

## Installation

```bash
pip3 install -U claw-swarm
```

---

## Environment variables

Set these in your shell or in a `.env` file (e.g. `--env-file .env` with Docker). Omit a platform’s credentials to disable that channel.

| Variable | Purpose | Default |
|----------|---------|---------|
| **Gateway** | | |
| `GATEWAY_HOST` | Bind address (gateway) or gateway host (agent) | `[::]` (server), `localhost` (agent) |
| `GATEWAY_PORT` | gRPC port | `50051` |
| `GATEWAY_TLS` | Enable TLS: `1`, `true`, or `yes` | — |
| `GATEWAY_TLS_CERT_FILE` | Path to TLS certificate file | — |
| `GATEWAY_TLS_KEY_FILE` | Path to TLS private key file | — |
| **Channels** | | |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token | — |
| `DISCORD_BOT_TOKEN` | Discord bot token | — |
| `DISCORD_CHANNEL_IDS` | Comma-separated Discord channel IDs | — |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API access token | — |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Cloud API phone number ID | — |
| `WHATSAPP_QUEUE_PATH` | Optional WhatsApp queue path | — |
| **Agent** | | |
| `AGENT_MODEL` | Swarms agent model | `gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI API key (for agent model) | — |
| `ANTHROPIC_API_KEY` | Anthropic API key (for Claude tool) | — |
| **Memory** | | |
| `AGENT_MEMORY_FILE` | Agent memory markdown filename (project root) | `agent_memory.md` |
| `AGENT_MEMORY_MAX_CHARS` | Max characters of memory to load into context | `100000` |

---

## Quick Start

**1. Set environment variables** for the channels you use (see **Environment variables** above for the full table).

**2. Run the full stack** (gateway + agent in one process group):

```bash
./run.sh
```

Or run each component in a separate terminal:

```bash
python -m claw_swarm.gateway    # terminal 1
python -m claw_swarm.main       # terminal 2
```

Use Ctrl+C to stop; `run.sh` stops both processes. For 24/7 operation, run under systemd or Docker.

**Docker:**

```bash
docker build -t clawswarm .
docker run --env-file .env clawswarm
```

Pass channel tokens and `AGENT_MODEL` via `--env-file .env` or `-e`.

---

## Configuration

See the **Environment variables** table above for the full list. The gateway and agent both read `GATEWAY_HOST` and `GATEWAY_PORT` (gateway binds on that address; agent connects to it). Replies use the same platform tokens as the gateway.


---

## Gateway API

The Messaging Gateway exposes a gRPC service (`MessagingGateway`) used by the agent runner:

- **PollMessages** — Fetch messages since a timestamp (used by the agent loop). Request: `platforms` (optional filter), `since_timestamp_utc_ms`, `max_messages`. Returns a batch of `UnifiedMessage`s.
- **StreamMessages** — Server-streaming delivery of new messages (optional alternative to polling).
- **Health** — Liveness and version for load balancers / readiness.

All messages are normalized to **UnifiedMessage** (id, platform, channel_id, thread_id, sender_id, sender_handle, text, attachment_urls, timestamp_utc_ms). Replies are sent by the **Replier** module via Telegram/Discord/WhatsApp HTTP APIs (same credentials as the gateway adapters), not via gRPC. Use TLS and restrict network access in production.

---

## Security and Operations

- **Secrets** — Do not commit tokens or API keys. Use environment variables or a secrets manager.
- **Transport** — Enable gateway TLS in production (`GATEWAY_TLS=1` and valid certificate and key).
- **Access control** — Restrict which clients can reach the gRPC port (firewall, VPC, or mTLS as required).

---

## License

See the repository LICENSE for terms of use.
