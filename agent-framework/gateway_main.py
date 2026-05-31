import asyncio
import argparse
import os
from agent_framework.gateway.core import GatewayCore


def main():
    parser = argparse.ArgumentParser(description="Start the Gateway server")
    parser.add_argument(
        "--host",
        default=os.environ.get("GATEWAY_HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1, use 0.0.0.0 only in trusted networks)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("GATEWAY_PORT", "18789")),
        help="Port to bind to (default: 18789)",
    )
    parser.add_argument(
        "--auth-secret",
        default=os.environ.get("GATEWAY_AUTH_SECRET"),
        help="JWT auth secret for WebSocket authentication",
    )
    args = parser.parse_args()

    # 安全警告：如果绑定到 0.0.0.0
    if args.host == "0.0.0.0":
        import warnings
        warnings.warn(
            "Binding to 0.0.0.0 exposes the gateway on all network interfaces. "
            "This should only be used in trusted networks or with proper firewall rules. "
            "Consider using 127.0.0.1 for local development.",
            SecurityWarning,
        )

    gateway = GatewayCore(
        host=args.host,
        port=args.port,
        auth_secret=args.auth_secret,
    )
    asyncio.run(gateway.start())


class SecurityWarning(Warning):
    pass


if __name__ == "__main__":
    main()
