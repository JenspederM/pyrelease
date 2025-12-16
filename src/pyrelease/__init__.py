import argparse
from pathlib import Path


def add_global_args(parser: argparse.ArgumentParser):
    global_args = parser.add_argument_group("global")
    global_args.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the git repository",
    )


def create_parser_from_files(path: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pyrelease", description="PyRelease CLI")
    sub_parser = parser.add_subparsers(dest="command")
    cli_commands = {}
    for f in path.glob("*.py"):
        if f.is_file() and f.stem != "__init__":
            module_path = f"pyrelease.commands.{f.stem}"
            module = __import__(module_path, fromlist=[""])
            if not hasattr(module, "register"):
                raise ImportError(
                    f"The module {f.stem} does not have a register function."
                )
            module_parser: argparse.ArgumentParser = module.register(sub_parser)
            add_global_args(module_parser)
            cli_commands[f.stem] = module
    return parser, cli_commands


def main():
    commands_path = Path(__file__).parent / "commands"
    parser, cli_commands = create_parser_from_files(commands_path)
    args = parser.parse_args()
    if args.command in cli_commands:
        command_module = cli_commands[args.command]
        if hasattr(command_module, "execute"):
            command_module.execute(args)
        else:
            raise ImportError(
                f"The module {args.command} does not have an execute function."
            )
    else:
        parser.print_help()


__all__ = ["main"]
