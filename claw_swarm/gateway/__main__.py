"""
Gateway entrypoint for: python -m claw_swarm.gateway
"""

from __future__ import annotations

import asyncio
import os

import grpc

from claw_swarm.gateway import (
    DiscordAdapter,
    TelegramAdapter,
    WhatsAppAdapter,
    run_server,
)


def main() -> None:
    adapters = [
        TelegramAdapter(),
        DiscordAdapter(),
        WhatsAppAdapter(),
    ]
    host = os.environ.get("GATEWAY_HOST", "[::]")
    port = int(os.environ.get("GATEWAY_PORT", "50051"))
    use_tls = os.environ.get("GATEWAY_TLS", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    server_credentials = None
    if use_tls:
        cert_file = os.environ.get("GATEWAY_TLS_CERT_FILE")
        key_file = os.environ.get("GATEWAY_TLS_KEY_FILE")
        if cert_file and key_file:
            with open(cert_file, "rb") as f:
                cert = f.read()
            with open(key_file, "rb") as f:
                key = f.read()
            server_credentials = grpc.ssl_server_credentials(
                ((key, cert),)
            )

    async def serve() -> None:
        srv = await run_server(
            adapters,
            host=host,
            port=port,
            use_tls=use_tls,
            server_credentials=server_credentials,
        )
        print(
            f"Messaging Gateway gRPC server listening on {host}:{port} (TLS={use_tls})"
        )
        await srv.wait_for_termination()

    asyncio.run(serve())


if __name__ == "__main__":
    main()
