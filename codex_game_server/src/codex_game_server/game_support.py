from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GameSupportProfile:
    game: str
    display_name: str
    integration_kind: str
    maturity: str
    default_port: int
    directories: dict[str, str]
    notes: tuple[str, ...]
    category: str = "game_server"
    aliases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "game": self.game,
            "display_name": self.display_name,
            "integration_kind": self.integration_kind,
            "maturity": self.maturity,
            "category": self.category,
            "aliases": list(self.aliases),
            "default_port": self.default_port,
            "directories": dict(self.directories),
            "commands": {
                "codex": "/codex *",
                "codex_func": "/codex_func *",
            },
            "notes": list(self.notes),
        }


SUPPORTED_GAMES: dict[str, GameSupportProfile] = {
    "minecraft": GameSupportProfile(
        game="minecraft",
        display_name="Minecraft",
        integration_kind="paper_spigot_plugin_scaffold",
        maturity="testable_scaffold",
        default_port=25565,
        directories={
            "world": "world",
            "plugins": "plugins",
            "backups": "backups",
            "logs": "logs",
        },
        notes=(
            "Generates a Paper/Spigot Java plugin skeleton with /codex and /codex_func commands.",
            "The generated plugin forwards admin player requests to the local Python bridge.",
        ),
    ),
    "project_zomboid": GameSupportProfile(
        game="project_zomboid",
        display_name="Project Zomboid",
        integration_kind="server_mod_scaffold",
        maturity="testable_scaffold",
        default_port=16261,
        directories={
            "world": "Saves/Multiplayer",
            "plugins": "mods",
            "backups": "backups",
            "logs": "Logs",
        },
        notes=(
            "Generates a server mod skeleton and bridge configuration for admin command forwarding.",
            "The Lua hook is intentionally isolated so it can be adjusted to the server build under test.",
        ),
    ),
    "palworld": GameSupportProfile(
        game="palworld",
        display_name="Palworld",
        integration_kind="rcon_sidecar_scaffold",
        maturity="sidecar_scaffold",
        default_port=8211,
        directories={
            "world": "Pal/Saved/SaveGames",
            "plugins": "Pal/Content/Paks/~mods",
            "backups": "backups",
            "logs": "Pal/Saved/Logs",
        },
        notes=(
            "Generates a sidecar/RCON bridge scaffold because stock dedicated servers do not expose a stable Python plugin API.",
            "Use the generated relay notes to connect an approved admin command source to the Python bridge.",
        ),
    ),
    "terraria": GameSupportProfile(
        game="terraria",
        display_name="Terraria",
        integration_kind="tshock_plugin_scaffold",
        maturity="testable_scaffold",
        default_port=7777,
        directories={
            "world": "Worlds",
            "plugins": "ServerPlugins",
            "backups": "backups",
            "logs": "logs",
        },
        notes=(
            "Generates a TShock/TerrariaAPI C# plugin skeleton with /codex and /codex_func commands.",
            "The generated plugin forwards authorized player requests to the local Python bridge.",
        ),
    ),
    "roblox": GameSupportProfile(
        game="roblox",
        display_name="Roblox Studio",
        integration_kind="studio_plugin_scaffold",
        maturity="tool_scaffold",
        default_port=8766,
        directories={
            "world": "workspace",
            "plugins": "RobloxPlugins",
            "backups": "backups",
            "logs": "logs",
        },
        notes=(
            "Generates a Roblox Studio plugin scaffold that posts Codex prompts to the local Python bridge.",
            "Studio HTTP access must be enabled for the plugin test environment.",
        ),
        category="development_tool",
        aliases=("roblox_studio",),
    ),
    "mapleworld": GameSupportProfile(
        game="mapleworld",
        display_name="MapleStory Worlds",
        integration_kind="world_script_scaffold",
        maturity="tool_scaffold",
        default_port=8766,
        directories={
            "world": "workspace",
            "plugins": "MapleWorldScripts",
            "backups": "backups",
            "logs": "logs",
        },
        notes=(
            "Generates a MapleWorld script bridge scaffold for forwarding trusted creator/admin requests.",
            "The generated files document the local bridge contract so the exact editor hook can be adjusted during platform testing.",
        ),
        category="development_tool",
        aliases=("maple_world", "maplestory_worlds", "maple_story_worlds"),
    ),
    "unity": GameSupportProfile(
        game="unity",
        display_name="Unity Editor",
        integration_kind="unity_editor_extension_scaffold",
        maturity="tool_scaffold",
        default_port=8766,
        directories={
            "world": "Assets",
            "plugins": "Assets/Editor/CodexGameServer",
            "backups": "backups",
            "logs": "Logs",
        },
        notes=(
            "Generates a Unity EditorWindow scaffold for calling the local Codex bridge from editor tooling.",
            "The scaffold is editor-only and does not ship into runtime builds by default.",
        ),
        category="game_engine",
        aliases=("unity_editor",),
    ),
    "unreal": GameSupportProfile(
        game="unreal",
        display_name="Unreal Engine",
        integration_kind="unreal_editor_plugin_scaffold",
        maturity="tool_scaffold",
        default_port=8766,
        directories={
            "world": "Content",
            "plugins": "Plugins/CodexGameServer",
            "backups": "backups",
            "logs": "Saved/Logs",
        },
        notes=(
            "Generates an Unreal Editor plugin scaffold and local bridge contract files.",
            "The scaffold targets editor-side Codex assistance rather than packaged game runtime execution.",
        ),
        category="game_engine",
        aliases=("unreal_engine", "ue"),
    ),
}


def normalize_game(game: str) -> str:
    return game.strip().lower().replace("-", "_").replace(" ", "_")


def profile_for(game: str) -> GameSupportProfile:
    normalized = normalize_game(game)
    if normalized in SUPPORTED_GAMES:
        return SUPPORTED_GAMES[normalized]
    for profile in SUPPORTED_GAMES.values():
        aliases = {normalize_game(alias) for alias in profile.aliases}
        if normalized in aliases:
            return profile
    raise ValueError(f"unsupported game or tool target: {game}")


def profiles_payload() -> dict[str, Any]:
    return {"games": [profile.to_dict() for profile in sorted(SUPPORTED_GAMES.values(), key=lambda item: item.game)]}


def scaffold_files(profile: GameSupportProfile, *, bridge_url: str) -> dict[str, str]:
    if profile.game == "minecraft":
        return _minecraft_files(bridge_url)
    if profile.game == "project_zomboid":
        return _project_zomboid_files(bridge_url)
    if profile.game == "palworld":
        return _palworld_files(bridge_url)
    if profile.game == "terraria":
        return _terraria_files(bridge_url)
    if profile.game == "roblox":
        return _roblox_files(bridge_url)
    if profile.game == "mapleworld":
        return _mapleworld_files(bridge_url)
    if profile.game == "unity":
        return _unity_files(bridge_url)
    if profile.game == "unreal":
        return _unreal_files(bridge_url)
    raise ValueError(f"unsupported game or tool target: {profile.game}")


def write_scaffold(
    profile: GameSupportProfile,
    *,
    output_dir: Path,
    bridge_url: str,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    written: list[dict[str, Any]] = []
    for relative, content in scaffold_files(profile, bridge_url=bridge_url).items():
        target = output_dir / relative
        if target.exists() and not overwrite:
            raise ValueError(f"scaffold file already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append({"path": str(target), "bytes": len(content.encode("utf-8"))})
    return written


def _minecraft_files(bridge_url: str) -> dict[str, str]:
    return {
        "minecraft-paper/README.md": _readme(
            "Minecraft Paper/Spigot",
            bridge_url,
            "Build the plugin jar and copy it into the server plugins directory.",
        ),
        "minecraft-paper/plugin.yml": """name: CodexGameServer
version: 0.1.0
main: com.codexgameserver.CodexGameServerPlugin
api-version: "1.20"
commands:
  codex:
    description: Forward a prompt to Codex Game Server.
    usage: /codex <prompt>
    permission: codexgameserver.use
  codex_func:
    description: Run an internal Codex Game Server function.
    usage: /codex_func <function>
    permission: codexgameserver.admin
permissions:
  codexgameserver.use:
    default: op
  codexgameserver.admin:
    default: op
""",
        "minecraft-paper/config.yml": f"""bridge-url: "{bridge_url}"
request-timeout-ms: 30000
""",
        "minecraft-paper/build.gradle": """plugins {
    id 'java'
}

group = 'com.codexgameserver'
version = '0.1.0'

repositories {
    mavenCentral()
    maven { url = 'https://repo.papermc.io/repository/maven-public/' }
}

dependencies {
    compileOnly 'io.papermc.paper:paper-api:1.20.6-R0.1-SNAPSHOT'
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(17)
    }
}
""",
        "minecraft-paper/src/main/java/com/codexgameserver/CodexGameServerPlugin.java": """package com.codexgameserver;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;

public final class CodexGameServerPlugin extends JavaPlugin {
    private String bridgeUrl;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        bridgeUrl = getConfig().getString("bridge-url", "http://127.0.0.1:8766");
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!(sender instanceof Player)) {
            sender.sendMessage("CodexGameServer commands must be run by a player account.");
            return true;
        }
        Player player = (Player) sender;
        String body = String.join(" ", args).trim();
        if (body.isEmpty()) {
            player.sendMessage("Usage: /" + label + " <prompt>");
            return true;
        }
        String endpoint = label.equalsIgnoreCase("codex_func") ? "/v1/codex_func" : "/v1/codex";
        String field = label.equalsIgnoreCase("codex_func") ? "command" : "prompt";
        getServer().getScheduler().runTaskAsynchronously(this, () -> {
            try {
                String response = post(endpoint, player.getName(), field, body);
                player.sendMessage(response);
            } catch (Exception exc) {
                player.sendMessage("Codex bridge error: " + exc.getMessage());
            }
        });
        return true;
    }

    private String post(String endpoint, String account, String field, String value) throws Exception {
        URL url = new URL(bridgeUrl + endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);
        String payload = "{\"account\":\"" + escape(account) + "\",\"" + field + "\":\"" + escape(value) + "\"}";
        try (OutputStream os = conn.getOutputStream()) {
            os.write(payload.getBytes(StandardCharsets.UTF_8));
        }
        byte[] bytes = conn.getInputStream().readAllBytes();
        return new String(bytes, StandardCharsets.UTF_8);
    }

    private String escape(String value) {
        return value.replace("\\\\", "\\\\\\\\").replace("\"", "\\\\\"");
    }
}
""",
    }


def _project_zomboid_files(bridge_url: str) -> dict[str, str]:
    return {
        "project-zomboid-mod/README.md": _readme(
            "Project Zomboid server mod",
            bridge_url,
            "Copy the CodexGameServer mod directory into the server mods folder and enable it for the test server.",
        ),
        "project-zomboid-mod/CodexGameServer/mod.info": """name=CodexGameServer
id=CodexGameServer
description=Admin command bridge for Codex Game Server. Commands: /codex and /codex_func.
poster=poster.png
""",
        "project-zomboid-mod/CodexGameServer/media/lua/server/CodexGameServer.lua": f"""local CodexGameServer = {{}}

CodexGameServer.bridgeUrl = "{bridge_url}"
CodexGameServer.commandPrefix = "/codex "
CodexGameServer.functionPrefix = "/codex_func "

function CodexGameServer.onClientCommand(module, command, player, args)
    if module ~= "CodexGameServer" then
        return
    end
    -- Server builds differ in how chat/admin commands are exposed to Lua.
    -- Forward authorized admin commands from the active command hook to:
    --   POST /v1/codex      {{ account = player:getUsername(), prompt = "..." }}
    --   POST /v1/codex_func {{ account = player:getUsername(), command = "..." }}
    print("[CodexGameServer] received " .. tostring(command) .. " from " .. tostring(player:getUsername()))
end

Events.OnClientCommand.Add(CodexGameServer.onClientCommand)
""",
        "project-zomboid-mod/codex_bridge.json": f"""{{
  "bridge_url": "{bridge_url}",
  "command_prefix": "/codex",
  "function_prefix": "/codex_func"
}}
""",
    }


def _palworld_files(bridge_url: str) -> dict[str, str]:
    return {
        "palworld-sidecar/README.md": _readme(
            "Palworld sidecar bridge",
            bridge_url,
            "Use this as a local sidecar/RCON relay scaffold for a Palworld dedicated server.",
        )
        + "\nStock Palworld dedicated servers do not expose a stable native plugin command API. "
        + "This scaffold keeps the Python Codex bridge ready and documents the required relay contract for test servers.\n",
        "palworld-sidecar/codex_bridge.json": f"""{{
  "bridge_url": "{bridge_url}",
  "command_prefix": "/codex",
  "function_prefix": "/codex_func",
  "relay_mode": "rcon_or_mod_loader"
}}
""",
        "palworld-sidecar/PalWorldSettings.ini.patch": """; Enable RCON in the Palworld server settings before connecting a relay.
; RCONEnabled=True
; AdminPassword=<set-a-strong-password>
""",
    }


def _terraria_files(bridge_url: str) -> dict[str, str]:
    return {
        "terraria-tshock/README.md": _readme(
            "Terraria TShock plugin",
            bridge_url,
            "Build the plugin and place the assembly in the TShock ServerPlugins directory.",
        ),
        "terraria-tshock/CodexGameServerPlugin.cs": f"""using System;
using System.Net.Http;
using TerrariaApi.Server;
using TShockAPI;

[ApiVersion(2, 1)]
public class CodexGameServerPlugin : TerrariaPlugin
{{
    private readonly HttpClient client = new HttpClient();
    public override string Name => "CodexGameServer";
    public override string Author => "Codex Game Server contributors";
    public override string Description => "Admin command bridge for Codex Game Server.";
    public override Version Version => new Version(0, 1, 0);
    private const string BridgeUrl = "{bridge_url}";

    public CodexGameServerPlugin(Main game) : base(game) {{ }}

    public override void Initialize()
    {{
        Commands.ChatCommands.Add(new Command("codexgameserver.use", Codex, "codex"));
        Commands.ChatCommands.Add(new Command("codexgameserver.admin", CodexFunc, "codex_func"));
    }}

    private async void Codex(CommandArgs args)
    {{
        await Post(args, "/v1/codex", "prompt");
    }}

    private async void CodexFunc(CommandArgs args)
    {{
        await Post(args, "/v1/codex_func", "command");
    }}

    private async System.Threading.Tasks.Task Post(CommandArgs args, string endpoint, string field)
    {{
        string body = string.Join(" ", args.Parameters);
        string json = "{{\\"account\\":\\"" + args.Player.Name + "\\",\\"" + field + "\\":\\"" + body.Replace("\\"", "\\\\\\"") + "\\"}}";
        HttpContent content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
        HttpResponseMessage response = await client.PostAsync(BridgeUrl + endpoint, content);
        string responseText = await response.Content.ReadAsStringAsync();
        args.Player.SendInfoMessage(responseText);
    }}
}}
""",
    }


def _roblox_files(bridge_url: str) -> dict[str, str]:
    return {
        "roblox-studio-plugin/README.md": _readme(
            "Roblox Studio plugin",
            bridge_url,
            "Install the Lua plugin in Roblox Studio and enable HTTP requests for the test place.",
        )
        + "\nThis scaffold exposes Studio toolbar actions for Codex prompts and internal functions.\n",
        "roblox-studio-plugin/CodexGameServerPlugin.lua": f"""local HttpService = game:GetService("HttpService")

local BRIDGE_URL = "{bridge_url}"
local toolbar = plugin:CreateToolbar("Codex")
local codexButton = toolbar:CreateButton("Codex Prompt", "Send a prompt to Codex Game Server", "")
local funcButton = toolbar:CreateButton("Codex Func", "Run a Codex Game Server internal function", "")

local function post(endpoint, payload)
    local encoded = HttpService:JSONEncode(payload)
    return HttpService:PostAsync(BRIDGE_URL .. endpoint, encoded, Enum.HttpContentType.ApplicationJson)
end

codexButton.Click:Connect(function()
    -- Replace the placeholder account with a registered creator/admin identity.
    local response = post("/v1/codex", {{
        account = "studio-admin",
        prompt = "Review the selected Roblox Studio work and suggest next steps."
    }})
    print("[CodexGameServer] " .. tostring(response))
end)

funcButton.Click:Connect(function()
    local response = post("/v1/codex_func", {{
        account = "studio-admin",
        command = "status"
    }})
    print("[CodexGameServer] " .. tostring(response))
end)
""",
        "roblox-studio-plugin/codex_bridge.json": f"""{{
  "bridge_url": "{bridge_url}",
  "command_prefix": "/codex",
  "function_prefix": "/codex_func",
  "target": "roblox"
}}
""",
    }


def _mapleworld_files(bridge_url: str) -> dict[str, str]:
    return {
        "mapleworld-script/README.md": _readme(
            "MapleStory Worlds script bridge",
            bridge_url,
            "Use the script scaffold inside the world/editor test harness and wire the request functions to trusted creator/admin UI actions.",
        )
        + "\nThe exact editor hook can be adjusted during MapleWorld testing while preserving the bridge payload contract.\n",
        "mapleworld-script/CodexBridge.lua": f"""local CodexBridge = {{}}

CodexBridge.bridgeUrl = "{bridge_url}"
CodexBridge.commandPrefix = "/codex"
CodexBridge.functionPrefix = "/codex_func"

function CodexBridge.codex(account, prompt)
    -- Wire this function to a trusted creator/admin command UI in MapleWorld tests.
    return {{
        endpoint = "/v1/codex",
        account = account,
        prompt = prompt
    }}
end

function CodexBridge.codex_func(account, command)
    return {{
        endpoint = "/v1/codex_func",
        account = account,
        command = command
    }}
end

return CodexBridge
""",
        "mapleworld-script/codex_bridge.json": f"""{{
  "bridge_url": "{bridge_url}",
  "command_prefix": "/codex",
  "function_prefix": "/codex_func",
  "target": "mapleworld"
}}
""",
    }


def _unity_files(bridge_url: str) -> dict[str, str]:
    return {
        "unity-editor/README.md": _readme(
            "Unity Editor extension",
            bridge_url,
            "Copy `Assets/Editor/CodexGameServer` into a Unity project and open Tools/Codex Game Server.",
        ),
        "unity-editor/Assets/Editor/CodexGameServer/CodexBridgeWindow.cs": f"""using System;
using System.Net.Http;
using System.Text;
using UnityEditor;
using UnityEngine;

public class CodexBridgeWindow : EditorWindow
{{
    private const string BridgeUrl = "{bridge_url}";
    private string account = "unity-admin";
    private string prompt = "Review this Unity project context and suggest next steps.";
    private string functionCommand = "status";
    private string lastResponse = "";

    [MenuItem("Tools/Codex Game Server")]
    public static void Open()
    {{
        GetWindow<CodexBridgeWindow>("Codex Game Server");
    }}

    private void OnGUI()
    {{
        account = EditorGUILayout.TextField("Account", account);
        prompt = EditorGUILayout.TextField("Codex Prompt", prompt);
        functionCommand = EditorGUILayout.TextField("Function", functionCommand);

        if (GUILayout.Button("Send /codex"))
        {{
            Post("/v1/codex", "{{\\\"account\\\":\\\"" + account + "\\\",\\\"prompt\\\":\\\"" + Escape(prompt) + "\\\"}}");
        }}
        if (GUILayout.Button("Send /codex_func"))
        {{
            Post("/v1/codex_func", "{{\\\"account\\\":\\\"" + account + "\\\",\\\"command\\\":\\\"" + Escape(functionCommand) + "\\\"}}");
        }}

        EditorGUILayout.HelpBox(lastResponse, MessageType.Info);
    }}

    private async void Post(string endpoint, string json)
    {{
        using (var client = new HttpClient())
        {{
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await client.PostAsync(BridgeUrl + endpoint, content);
            lastResponse = await response.Content.ReadAsStringAsync();
            Repaint();
        }}
    }}

    private static string Escape(string value)
    {{
        return value.Replace("\\\\", "\\\\\\\\").Replace("\\\"", "\\\\\\\"");
    }}
}}
""",
        "unity-editor/codex_bridge.json": f"""{{
  "bridge_url": "{bridge_url}",
  "command_prefix": "/codex",
  "function_prefix": "/codex_func",
  "target": "unity"
}}
""",
    }


def _unreal_files(bridge_url: str) -> dict[str, str]:
    return {
        "unreal-plugin/README.md": _readme(
            "Unreal Engine editor plugin",
            bridge_url,
            "Copy `Plugins/CodexGameServer` into an Unreal project and build the editor module.",
        ),
        "unreal-plugin/Plugins/CodexGameServer/CodexGameServer.uplugin": """{
  "FileVersion": 3,
  "Version": 1,
  "VersionName": "0.1.0",
  "FriendlyName": "Codex Game Server",
  "Description": "Editor-side bridge scaffold for Codex Game Server.",
  "Category": "Editor",
  "Modules": [
    {
      "Name": "CodexGameServer",
      "Type": "Editor",
      "LoadingPhase": "Default"
    }
  ]
}
""",
        "unreal-plugin/Plugins/CodexGameServer/Source/CodexGameServer/CodexGameServer.Build.cs": """using UnrealBuildTool;

public class CodexGameServer : ModuleRules
{
    public CodexGameServer(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(new string[] {
            "Core",
            "CoreUObject",
            "Engine",
            "HTTP",
            "Json",
            "UnrealEd"
        });
    }
}
""",
        "unreal-plugin/Plugins/CodexGameServer/Source/CodexGameServer/Private/CodexGameServerModule.cpp": f"""#include "Modules/ModuleManager.h"

class FCodexGameServerModule final : public IModuleInterface
{{
public:
    virtual void StartupModule() override
    {{
        // Register editor commands or toolbar actions here.
        // Forward trusted editor/admin prompts to:
        //   POST {bridge_url}/v1/codex
        //   POST {bridge_url}/v1/codex_func
    }}
}};

IMPLEMENT_MODULE(FCodexGameServerModule, CodexGameServer)
""",
        "unreal-plugin/codex_bridge.json": f"""{{
  "bridge_url": "{bridge_url}",
  "command_prefix": "/codex",
  "function_prefix": "/codex_func",
  "target": "unreal"
}}
""",
    }


def _readme(title: str, bridge_url: str, install_note: str) -> str:
    return f"""# Codex Game Server - {title}

This generated scaffold connects in-game admin commands to the local Python bridge.

- `/codex *` forwards a prompt to Codex.
- `/codex_func *` runs an internal server-management function.
- Bridge URL: `{bridge_url}`

{install_note}

Before testing, register the in-game administrator account:

```bash
cgs admin add <server-path> --account <in-game-name>
cgs bridge serve <server-path>
```
"""
