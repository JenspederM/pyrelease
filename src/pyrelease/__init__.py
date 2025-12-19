import argparse
import importlib
import sys
from collections.abc import Callable
from pathlib import Path

from pyrelease.utils import add_global_args, get_additional_args, read_pyrelease_config


def load_command_module(command_name: str):
    module_path = f"pyrelease.commands.{command_name}"
    module = importlib.import_module(module_path)
    if not hasattr(module, "register"):  # pragma: no cover - we trust importlib
        raise ImportError(
            f"The module {command_name} does not have a register function."
        )
    if not hasattr(module, "execute"):  # pragma: no cover - we trust importlib
        raise ImportError(
            f"The module {command_name} does not have an execute function."
        )
    return module


def create_parser_from_files(
    path: Path,
) -> tuple[
    argparse.ArgumentParser,
    dict[str, tuple[Callable[[argparse.Namespace], None], argparse.ArgumentParser]],
]:
    parser = argparse.ArgumentParser(
        prog="pyrelease",
        description="PyRelease CLI is a tool to manage Python project releases.",
        usage="pyrelease <command> [options]",
    )
    sub_parser = parser.add_subparsers(dest="command")
    add_global_args(parser)
    cli_commands = {}
    for f in path.glob("*.py"):
        if f.is_file() and f.stem != "__init__":
            module = load_command_module(f.stem)
            module_parser: argparse.ArgumentParser = module.register(sub_parser)
            module_executor: Callable[[argparse.Namespace], None] = module.execute
            add_global_args(module_parser)
            cli_commands[f.stem] = (module_executor, module_parser)
    parser._positionals.title = "commands"
    return parser, cli_commands


def main(sys_args: list[str] | None = None):
    try:
        commands_path = Path(__file__).parent / "commands"
        parser, cli_commands = create_parser_from_files(commands_path)
        # sys_argv[0] is the script name, so we skip it
        sys_args = sys.argv[1:] if sys_args is None else sys_args
        args = parser.parse_args(sys_args)
        config_args = read_pyrelease_config(args.path)
        if args.command in cli_commands:
            additional_args = get_additional_args(config_args, args.command)
            command_executor, command_parser = cli_commands[args.command]
            # sys_argv[0] is the command name, so we skip it
            command_args = additional_args + sys_args[1:]
            if args.debug:  # pragma: no cover - only for debugging
                print(  # noqa: T201
                    f"Debug: Executing command '{args.command}':\n"
                    f"    sys_args={sys_args},\n"
                    f"    additional_args={additional_args},\n"
                    f"    command_args={command_args}\n",
                )
            known_args, _ = command_parser.parse_known_args(command_args)
            command_executor(known_args)
        else:
            parser.print_help()
    except SystemExit as e:
        if e.code != 0:
            raise e


__all__ = ["main"]
