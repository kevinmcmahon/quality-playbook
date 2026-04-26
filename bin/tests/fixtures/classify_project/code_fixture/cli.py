"""cli.py -- entry point for the Code classifier fixture's calculator module."""

from __future__ import annotations

import argparse
import sys

from calculator import RunningStats, mean, variance


def parse_values(raw: str) -> list[float]:
    values: list[float] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        values.append(float(token))
    return values


def cmd_mean(args: argparse.Namespace) -> int:
    values = parse_values(args.values)
    print(mean(values))
    return 0


def cmd_variance(args: argparse.Namespace) -> int:
    values = parse_values(args.values)
    print(variance(values))
    return 0


def cmd_streaming(args: argparse.Namespace) -> int:
    stats = RunningStats()
    for value in parse_values(args.values):
        stats.push(value)
    print(f"count={stats.count} mean={stats.mean} variance={stats.variance}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="calc")
    sub = parser.add_subparsers(required=True, dest="command")

    p_mean = sub.add_parser("mean")
    p_mean.add_argument("values")
    p_mean.set_defaults(func=cmd_mean)

    p_var = sub.add_parser("variance")
    p_var.add_argument("values")
    p_var.set_defaults(func=cmd_variance)

    p_stream = sub.add_parser("streaming")
    p_stream.add_argument("values")
    p_stream.set_defaults(func=cmd_streaming)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
