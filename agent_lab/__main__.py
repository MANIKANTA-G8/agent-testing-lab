import argparse
import json
from .core import run_suite, save_run


def main():
    parser = argparse.ArgumentParser(description="Agent Testing Lab • offline simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--variant", choices=["baseline", "improved"], default="improved")
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument("--output", default="runs")
    run.add_argument("--fail-on-error", action="store_true")
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command == "serve":
        from .server import serve
        serve(args.port)
    else:
        try:
            result = run_suite(args.variant, args.repeats)
        except ValueError as error:
            parser.error(str(error))
        path = save_run(result, args.output)
        print(json.dumps(result["summary"], indent=2))
        print(f"Evidence: {path}")
        if args.fail_on_error and result["summary"]["failed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
