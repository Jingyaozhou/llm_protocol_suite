"""Command-line entry point for LLM usage help."""

from __future__ import annotations

import argparse

from .usage import help_for, list_topics, llm_usage


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m llm_protocol_suite")
    subparsers = parser.add_subparsers(dest="command")

    usage_parser = subparsers.add_parser("usage", help="Print LLM usage help")
    usage_parser.add_argument("topic", nargs="?", default="index")

    subparsers.add_parser("topics", help="List LLM usage help topics")

    args = parser.parse_args()
    if args.command == "topics":
        print("\n".join(list_topics()))
        return
    if args.command == "usage":
        print(help_for(args.topic))
        return

    print(llm_usage())


if __name__ == "__main__":
    main()
