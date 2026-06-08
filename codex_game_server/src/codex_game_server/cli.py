from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from codex_game_server.accounts import add_admin, list_admins, remove_admin
from codex_game_server.bridge import codex_func_request, codex_request, serve_bridge
from codex_game_server.codex_runtime import check_codex_login
from codex_game_server.operations import (
    check_health,
    create_backup,
    init_server,
    inspect_server,
    list_plugins,
    run_server,
    scaffold_integration,
    supported_games,
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-game-server",
        description="Bridge Codex into game servers, game platforms, and game development tools.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    init = subcommands.add_parser("init", help="create a new server manifest")
    init.add_argument("path", help="server root directory")
    init.add_argument("--name", default=None, help="server name; defaults to the directory name")
    init.add_argument("--game", default="generic", help="game or server family")
    init.add_argument("--host", default="127.0.0.1", help="host for health checks")
    init.add_argument("--port", type=int, default=None, help="server TCP port")
    init.add_argument("--start-command", default="", help="foreground launch command")
    init.add_argument("--overwrite", action="store_true", help="replace an existing manifest")
    init.add_argument("--json", action="store_true", help="print JSON")
    init.set_defaults(func=_cmd_init)

    inspect = subcommands.add_parser("inspect", help="inspect manifest, directories, plugins, and backups")
    inspect.add_argument("path", help="server root directory or manifest path")
    inspect.add_argument("--with-health", action="store_true", help="include a TCP health probe")
    inspect.add_argument("--json", action="store_true", help="print JSON")
    inspect.set_defaults(func=_cmd_inspect)

    plugins = subcommands.add_parser("plugins", help="list files in the configured plugin/mod directory")
    plugins.add_argument("path", help="server root directory or manifest path")
    plugins.add_argument("--json", action="store_true", help="print JSON")
    plugins.set_defaults(func=_cmd_plugins)

    health = subcommands.add_parser("health", help="check whether the configured TCP port accepts connections")
    health.add_argument("path", help="server root directory or manifest path")
    health.add_argument("--timeout", type=float, default=1.0, help="socket timeout in seconds")
    health.add_argument("--json", action="store_true", help="print JSON")
    health.set_defaults(func=_cmd_health)

    backup = subcommands.add_parser("backup", help="zip the configured world directory")
    backup.add_argument("path", help="server root directory or manifest path")
    backup.add_argument("--label", default="manual", help="backup label")
    backup.add_argument("--json", action="store_true", help="print JSON")
    backup.set_defaults(func=_cmd_backup)

    run = subcommands.add_parser("run", help="run the configured start command in the foreground")
    run.add_argument("path", help="server root directory or manifest path")
    run.add_argument("--dry-run", action="store_true", help="show the resolved launch without starting")
    run.add_argument("--json", action="store_true", help="print JSON for dry-run output")
    run.set_defaults(func=_cmd_run)

    games = subcommands.add_parser("games", help="list compatible game and tool targets")
    games.add_argument("--json", action="store_true", help="print JSON")
    games.set_defaults(func=_cmd_targets)

    targets = subcommands.add_parser("targets", help="list compatible game and development-tool targets")
    targets.add_argument("--json", action="store_true", help="print JSON")
    targets.set_defaults(func=_cmd_targets)

    integrate = subcommands.add_parser("integrate", help="generate game/plugin/tool bridge scaffold")
    integrate.add_argument("path", help="server root directory or manifest path")
    integrate.add_argument("--game", default=None, help="override manifest game profile")
    integrate.add_argument("--output", default=None, help="output directory; defaults to <server>/codex_integration")
    integrate.add_argument("--overwrite", action="store_true", help="replace existing scaffold files")
    integrate.add_argument("--json", action="store_true", help="print JSON")
    integrate.set_defaults(func=_cmd_integrate)

    codex = subcommands.add_parser("codex", help="inspect local Codex CLI readiness")
    codex_subcommands = codex.add_subparsers(dest="codex_command", required=True)
    codex_status = codex_subcommands.add_parser("status", help="check Codex installation and login")
    codex_status.add_argument("--doctor", action="store_true", help="include codex doctor --json")
    codex_status.add_argument("--json", action="store_true", help="print JSON")
    codex_status.set_defaults(func=_cmd_codex_status)

    admin = subcommands.add_parser("admin", help="manage in-game accounts allowed to call Codex")
    admin_subcommands = admin.add_subparsers(dest="admin_command", required=True)
    admin_add = admin_subcommands.add_parser("add", help="register an in-game administrator account")
    admin_add.add_argument("path", help="server root directory or manifest path")
    admin_add.add_argument("--account", required=True, help="game account id or in-game nickname")
    admin_add.add_argument("--display-name", default=None, help="human-readable display name")
    admin_add.add_argument("--role", action="append", dest="roles", help="role to assign; repeatable")
    admin_add.add_argument("--game", default=None, help="override manifest game profile")
    admin_add.add_argument("--json", action="store_true", help="print JSON")
    admin_add.set_defaults(func=_cmd_admin_add)

    admin_list = admin_subcommands.add_parser("list", help="list registered administrator accounts")
    admin_list.add_argument("path", help="server root directory or manifest path")
    admin_list.add_argument("--json", action="store_true", help="print JSON")
    admin_list.set_defaults(func=_cmd_admin_list)

    admin_remove = admin_subcommands.add_parser("remove", help="remove a registered administrator account")
    admin_remove.add_argument("path", help="server root directory or manifest path")
    admin_remove.add_argument("--account", required=True, help="game account id or in-game nickname")
    admin_remove.add_argument("--game", default=None, help="override manifest game profile")
    admin_remove.add_argument("--json", action="store_true", help="print JSON")
    admin_remove.set_defaults(func=_cmd_admin_remove)

    bridge = subcommands.add_parser("bridge", help="run or test the local Codex bridge")
    bridge_subcommands = bridge.add_subparsers(dest="bridge_command", required=True)
    bridge_serve = bridge_subcommands.add_parser("serve", help="serve the local HTTP bridge for game plugins")
    bridge_serve.add_argument("path", help="server root directory or manifest path")
    bridge_serve.add_argument("--host", default=None, help="bind host")
    bridge_serve.add_argument("--port", type=int, default=None, help="bind port")
    bridge_serve.add_argument("--no-codex-check", action="store_true", help="start without checking codex login first")
    bridge_serve.add_argument("--dry-run", action="store_true", help="accept prompts without calling Codex")
    bridge_serve.set_defaults(func=_cmd_bridge_serve)

    bridge_prompt = bridge_subcommands.add_parser("prompt", help="simulate /codex from an in-game account")
    bridge_prompt.add_argument("path", help="server root directory or manifest path")
    bridge_prompt.add_argument("--account", required=True, help="game account id or in-game nickname")
    bridge_prompt.add_argument("--prompt", required=True, help="prompt text")
    bridge_prompt.add_argument("--dry-run", action="store_true", help="accept prompt without calling Codex")
    bridge_prompt.add_argument("--json", action="store_true", help="print JSON")
    bridge_prompt.set_defaults(func=_cmd_bridge_prompt)

    bridge_func = bridge_subcommands.add_parser("func", help="simulate /codex_func from an in-game account")
    bridge_func.add_argument("path", help="server root directory or manifest path")
    bridge_func.add_argument("--account", required=True, help="game account id or in-game nickname")
    bridge_func.add_argument("--command", required=True, help="internal function command")
    bridge_func.add_argument("--json", action="store_true", help="print JSON")
    bridge_func.set_defaults(func=_cmd_bridge_func)

    return parser


def _cmd_init(args: argparse.Namespace) -> int:
    start_command = shlex.split(args.start_command) if args.start_command else []
    manifest = init_server(
        Path(args.path),
        name=args.name,
        game=args.game,
        host=args.host,
        port=args.port,
        start_command=start_command,
        overwrite=args.overwrite,
    )
    payload = {
        "manifest_path": str(manifest.manifest_path),
        "server": manifest.to_dict(),
    }

    if args.json:
        _print_json(payload)
        return 0

    print(f"created: {manifest.manifest_path}")
    print(f"server: {manifest.name} ({manifest.game})")
    print(f"address: {manifest.host}:{manifest.port}")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    payload = inspect_server(Path(args.path), include_health=args.with_health)
    if args.json:
        _print_json(payload)
        return 0

    print(f"{payload['name']} ({payload['game']})")
    print(f"manifest: {payload['manifest_path']}")
    print(f"address: {payload['host']}:{payload['port']}")
    print(f"plugins: {payload['plugin_count']}")
    print(f"backups: {payload['backup_count']}")
    port = payload["port_availability"]
    print(f"port_available: {port['available']}")
    if payload.get("health"):
        print(f"health: {payload['health']['status']}")
    return 0


def _cmd_plugins(args: argparse.Namespace) -> int:
    payload = {"plugins": list_plugins(Path(args.path))}
    if args.json:
        _print_json(payload)
        return 0

    if not payload["plugins"]:
        print("no plugins found")
        return 0

    for plugin in payload["plugins"]:
        print(f"{plugin['name']} {plugin['kind']} {plugin['size_bytes']} bytes")
    return 0


def _cmd_health(args: argparse.Namespace) -> int:
    payload = check_health(Path(args.path), timeout=args.timeout)
    if args.json:
        _print_json(payload)
    else:
        print(f"{payload['host']}:{payload['port']} {payload['status']}")
        if payload.get("error"):
            print(f"error: {payload['error']}")
    return 0 if payload["status"] == "open" else 1


def _cmd_backup(args: argparse.Namespace) -> int:
    payload = create_backup(Path(args.path), label=args.label)
    if args.json:
        _print_json(payload)
        return 0

    print(f"backup: {payload['path']}")
    print(f"files: {payload['file_count']}")
    print(f"bytes: {payload['size_bytes']}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_server(Path(args.path), dry_run=args.dry_run)
    if args.dry_run and args.json:
        _print_json(result)
        return 0

    if args.dry_run:
        print(f"cwd: {result['cwd']}")
        print(f"command: {result['command']}")
        return 0

    return int(result["return_code"])


def _cmd_targets(args: argparse.Namespace) -> int:
    payload = supported_games()
    if args.json:
        _print_json(payload)
        return 0

    for game in payload["games"]:
        print(f"{game['game']}: {game['display_name']}")
        print(f"  category: {game['category']}")
        print(f"  integration: {game['integration_kind']}")
        print(f"  commands: {game['commands']['codex']}, {game['commands']['codex_func']}")
    return 0


def _cmd_integrate(args: argparse.Namespace) -> int:
    payload = scaffold_integration(
        Path(args.path),
        output=Path(args.output) if args.output else None,
        game=args.game,
        overwrite=args.overwrite,
    )
    if args.json:
        _print_json(payload)
        return 0

    print(f"game: {payload['game']}")
    print(f"integration: {payload['integration_kind']}")
    print(f"output: {payload['output_dir']}")
    for item in payload["files"]:
        print(f"  wrote: {item['path']}")
    return 0


def _cmd_codex_status(args: argparse.Namespace) -> int:
    payload = check_codex_login(include_doctor=args.doctor)
    if args.json:
        _print_json(payload)
        return 0 if payload["available"] and payload["authenticated"] else 1

    print(f"available: {payload['available']}")
    print(f"authenticated: {payload['authenticated']}")
    print(f"version: {payload['version']}")
    if payload.get("error"):
        print(f"error: {payload['error']}")
    return 0 if payload["available"] and payload["authenticated"] else 1


def _cmd_admin_add(args: argparse.Namespace) -> int:
    admin = add_admin(
        Path(args.path),
        account=args.account,
        display_name=args.display_name,
        roles=args.roles,
        game=args.game,
    )
    payload = {"admin": admin}
    if args.json:
        _print_json(payload)
        return 0

    print(f"registered: {admin['game']}:{admin['account']}")
    print(f"roles: {', '.join(admin['roles'])}")
    return 0


def _cmd_admin_list(args: argparse.Namespace) -> int:
    payload = {"admins": list_admins(Path(args.path))}
    if args.json:
        _print_json(payload)
        return 0

    if not payload["admins"]:
        print("no admins registered")
        return 0
    for admin in payload["admins"]:
        state = "active" if admin["active"] else "inactive"
        print(f"{admin['game']}:{admin['account']} {state} roles={','.join(admin['roles'])}")
    return 0


def _cmd_admin_remove(args: argparse.Namespace) -> int:
    payload = remove_admin(Path(args.path), account=args.account, game=args.game)
    if args.json:
        _print_json(payload)
        return 0

    print(f"removed: {payload['removed']}")
    return 0


def _cmd_bridge_serve(args: argparse.Namespace) -> int:
    print("starting Codex Game Server bridge")
    serve_bridge(
        Path(args.path),
        host=args.host,
        port=args.port,
        require_codex_login=not args.no_codex_check,
        dry_run=args.dry_run,
    )
    return 0


def _cmd_bridge_prompt(args: argparse.Namespace) -> int:
    payload = codex_request(Path(args.path), account=args.account, prompt=args.prompt, dry_run=args.dry_run)
    if args.json:
        _print_json(payload)
    else:
        print(payload["message"])
    return 0 if payload["ok"] else 1


def _cmd_bridge_func(args: argparse.Namespace) -> int:
    payload = codex_func_request(Path(args.path), account=args.account, command=args.command)
    if args.json:
        _print_json(payload)
    else:
        print(payload["message"])
    return 0 if payload["ok"] else 1


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
