# Codex Game Server

Codex Game Server is a dependency-free Python CLI for game server operators,
game platform creators, and game-tool developers who want to expose Codex to
trusted in-game or editor-side administrators. It keeps a target declaration in
one JSON manifest, checks local Codex login status, registers authorized game
or tool accounts, generates target-specific integration scaffolds, and runs a
local HTTP bridge for `/codex *` and `/codex_func *` calls.

It also keeps the earlier server-ops helpers: plugin inventory, world backups,
TCP health checks, and foreground launches.

## Quick Start

```bash
python -m pip install -e .
cgs codex status
cgs init ./servers/survival \
  --name survival \
  --game minecraft \
  --port 25565 \
  --start-command "java -Xmx2G -jar server.jar nogui"
cgs admin add ./servers/survival --account Steve --display-name "Server Owner"
cgs integrate ./servers/survival
cgs bridge prompt ./servers/survival --account Steve --prompt "Check this server plan" --dry-run
cgs bridge serve ./servers/survival
cgs inspect ./servers/survival
```

The long command name is also available:

```bash
codex-game-server inspect ./servers/survival --json
```

## Manifest

`cgs init` creates `server.json`:

```json
{
  "schema_version": 1,
  "name": "survival",
  "game": "minecraft",
  "host": "127.0.0.1",
  "port": 25565,
  "start_command": ["java", "-Xmx2G", "-jar", "server.jar", "nogui"],
  "working_directory": ".",
  "directories": {
    "world": "world",
    "plugins": "plugins",
    "backups": "backups",
    "logs": "logs"
  },
  "codex": {
    "bridge_host": "127.0.0.1",
    "bridge_port": 8766,
    "command_prefix": "/codex",
    "function_prefix": "/codex_func",
    "require_admin": true
  },
  "env": {},
  "tags": [],
  "metadata": {}
}
```

All relative paths are resolved from the manifest directory.

## Codex Bridge

The Python bridge is the only component that talks to Codex. Game plugins,
mods, platform scripts, and editor extensions forward trusted commands to the
bridge:

- `/codex *`: send a prompt to Codex through `codex exec`
- `/codex_func *`: run internal server functions such as `status`, `admins`,
  `plugins`, `health`, and `backup <label>`

The bridge checks that the Codex CLI is installed and logged in before serving:

```bash
cgs codex status
cgs bridge serve ./servers/survival
```

For local testing without calling Codex:

```bash
cgs bridge prompt ./servers/survival \
  --account Steve \
  --prompt "Summarize the current server setup" \
  --dry-run
```

## Administrator Accounts

Only registered in-game accounts can call the bridge.

```bash
cgs admin add ./servers/survival --account Steve --display-name "Server Owner"
cgs admin list ./servers/survival
cgs admin remove ./servers/survival --account Steve
```

The registry is stored next to `server.json` as `codex_admins.json`.

## Supported Targets

Current test targets:

| Target | Category | Integration shape | Default command prefixes |
| --- | --- | --- | --- |
| Minecraft | Game server | Paper/Spigot plugin scaffold | `/codex`, `/codex_func` |
| Project Zomboid | Game server | Server mod scaffold | `/codex`, `/codex_func` |
| Palworld | Game server | Sidecar/RCON relay scaffold | `/codex`, `/codex_func` |
| Terraria | Game server | TShock/TerrariaAPI plugin scaffold | `/codex`, `/codex_func` |
| Roblox Studio | Development tool | Studio plugin scaffold | `/codex`, `/codex_func` |
| MapleStory Worlds | Development tool | World script scaffold | `/codex`, `/codex_func` |
| Unity Editor | Game engine | EditorWindow scaffold | `/codex`, `/codex_func` |
| Unreal Engine | Game engine | Editor plugin scaffold | `/codex`, `/codex_func` |

The supported target list is expected to keep changing as test coverage,
platform APIs, and integration details are updated.

Generate the current integration files:

```bash
cgs targets
cgs integrate ./servers/survival
```

## Commands

```bash
cgs init <path> [--name NAME] [--game GAME] [--port PORT] [--start-command COMMAND]
cgs games [--json]
cgs targets [--json]
cgs codex status [--doctor] [--json]
cgs admin add <path> --account ACCOUNT [--display-name NAME]
cgs admin list <path> [--json]
cgs admin remove <path> --account ACCOUNT
cgs integrate <path> [--game GAME] [--output DIR] [--overwrite]
cgs bridge serve <path> [--host HOST] [--port PORT] [--dry-run]
cgs bridge prompt <path> --account ACCOUNT --prompt PROMPT [--dry-run]
cgs bridge func <path> --account ACCOUNT --command COMMAND
cgs inspect <path> [--json]
cgs plugins <path> [--json]
cgs health <path> [--timeout SECONDS] [--json]
cgs backup <path> [--label LABEL] [--json]
cgs run <path> [--dry-run]
```

`run` launches the configured command in the foreground. Use `--dry-run` to
confirm the resolved command and working directory without starting anything.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests
```

## License

MIT
