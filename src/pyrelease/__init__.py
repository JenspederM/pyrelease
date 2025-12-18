import argparse
import importlib
from pathlib import Path
import sys
from typing import Callable

from pyrelease.utils import read_pyrelease_config


def add_global_args(parser: argparse.ArgumentParser):
    global_args = parser.add_argument_group("global")
    global_args.add_argument(
        "--project-name",
        type=str,
        help="Name of the project",
    )
    global_args.add_argument(
        "--project-version",
        type=str,
        help="Version of the project",
    )
    global_args.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the git repository",
    )
    global_args.add_argument(
        "--silent",
        action="store_true",
        help="Suppress output to stdout",
        default=False,
    )


def create_parser_from_files(
    path: Path,
) -> tuple[
    argparse.ArgumentParser,
    dict[str, tuple[Callable[[argparse.Namespace], None], argparse.ArgumentParser]],
]:
    parser = argparse.ArgumentParser(prog="pyrelease", description="PyRelease CLI")
    sub_parser = parser.add_subparsers(dest="command")
    cli_commands = {}
    for f in path.glob("*.py"):
        if f.is_file() and f.stem != "__init__":
            module_path = f"pyrelease.commands.{f.stem}"
            module = importlib.import_module(module_path)
            if not hasattr(module, "register"):
                raise ImportError(
                    f"The module {f.stem} does not have a register function."
                )
            if not hasattr(module, "execute"):
                raise ImportError(
                    f"The module {f.stem} does not have an execute function."
                )
            module_parser: argparse.ArgumentParser = module.register(sub_parser)
            module_executor: Callable[[argparse.Namespace], None] = module.execute
            add_global_args(module_parser)
            cli_commands[f.stem] = (module_executor, module_parser)
    return parser, cli_commands


def main(sys_args: list[str] | None = None):
    commands_path = Path(__file__).parent / "commands"
    parser, cli_commands = create_parser_from_files(commands_path)
    sys_args = sys.argv[1:] if sys_args is None else sys_args
    args = parser.parse_args(sys_args)
    config_args = read_pyrelease_config(args.path)
    if args.command in cli_commands:
        command_executor, command_parser = cli_commands[args.command]
        known_args, _ = command_parser.parse_known_args(config_args + sys_args)
        command_executor(known_args)
    else:
        parser.print_help()


__all__ = ["main"]
