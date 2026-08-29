from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .batch import write_batch
from .config import load_config
from .generator import generate_events
from .publishers import DryRunPublisher, MqttPublisher
from .streaming import stream_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Avahi-compatible synthetic telemetry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a finite batch sample")
    generate.add_argument("--config", required=True, help="Path to the JSON configuration")
    generate.add_argument("--output", default="output", help="Output directory")
    generate.add_argument("--duration", type=float, help="Override duration in seconds")
    generate.add_argument("--preview", type=int, default=3, help="Events to print")

    stream = subparsers.add_parser("stream", help="Stream events through MQTT or dry-run")
    stream.add_argument("--config", required=True, help="Path to the JSON configuration")
    stream.add_argument("--duration", type=float, help="Override duration in seconds")
    stream.add_argument("--dry-run", action="store_true", help="Print without network access")
    stream.add_argument("--no-wait", action="store_true", help="Do not sleep between cadences")
    stream.add_argument("--endpoint", help="AWS IoT Core endpoint")
    stream.add_argument("--port", type=int, default=8883)
    stream.add_argument("--client-id", default="minelogx-synthetic-generator")
    stream.add_argument("--ca", help="Path to the AWS IoT root CA")
    stream.add_argument("--cert", help="Path to the client certificate")
    stream.add_argument("--key", help="Path to the client private key")
    return parser


def run_generate(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    events = list(generate_events(config, duration_seconds=args.duration))
    paths = write_batch(events, args.output)

    for event in events[: max(args.preview, 0)]:
        print(json.dumps(event, indent=2))
    print(f"Generated {len(events)} events from {len(config.assets)} assets")
    for kind, path in paths.items():
        print(f"{kind}: {Path(path).resolve()}")
    return 0


def run_stream(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.dry_run:
        publisher = DryRunPublisher()
    else:
        missing = [
            name
            for name in ("endpoint", "ca", "cert", "key")
            if not getattr(args, name)
        ]
        if missing:
            raise SystemExit(f"Live MQTT requires: {', '.join('--' + name for name in missing)}")
        publisher = MqttPublisher(
            endpoint=args.endpoint,
            port=args.port,
            client_id=args.client_id,
            ca_path=args.ca,
            cert_path=args.cert,
            key_path=args.key,
        )

    try:
        stats = stream_events(
            config,
            publisher,
            duration_seconds=args.duration,
            realtime=not args.no_wait,
        )
    finally:
        publisher.close()
    print(json.dumps(stats.__dict__, indent=2))
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    if args.command == "generate":
        return run_generate(args)
    if args.command == "stream":
        return run_stream(args)
    raise RuntimeError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
