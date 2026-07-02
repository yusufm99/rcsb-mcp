# Additional setups

These guides explain how to connect `rcsb-mcp` to clients other than Claude
Desktop. They use the published `rcsb-mcp` package and do not require a local
repository checkout.

For the primary Claude Desktop setup, see the project
[README](../README.md#connect-to-claude-desktop).

## Table of contents

* [Connect to Codex Desktop on Windows](#connect-to-codex-desktop-on-windows)

  * [1. Find `uv.exe`](#1-find-uvexe)
  * [2. Open the Codex configuration](#2-open-the-codex-configuration)
  * [3. Test the connection](#3-test-the-connection)
* [Connect to LM Studio on Windows](#connect-to-lm-studio-on-windows)

  * [1. Download a tool-capable model](#1-download-a-tool-capable-model)
  * [2. Configure the MCP server](#2-configure-the-mcp-server)
  * [3. Limit the enabled tools for small models](#3-limit-the-enabled-tools-for-small-models)
  * [4. Test an IHM search](#4-test-an-ihm-search)
  * [Troubleshooting](#troubleshooting)

    * [The model returns no content](#the-model-returns-no-content)
    * [The model fails to generate a tool call](#the-model-fails-to-generate-a-tool-call)
    * [The model fails to load](#the-model-fails-to-load)
    * [Context usage exceeds 100%](#context-usage-exceeds-100)
* [Other model options](#other-model-options)

  * [Gemini](#gemini)
  * [Qwen](#qwen)
  * [DeepSeek](#deepseek)

## Connect to Codex Desktop on Windows

The Codex desktop app can use local MCP servers through:

```text
%USERPROFILE%\.codex\config.toml
```

The Codex CLI is not required for this setup.

### 1. Find `uv.exe`

In PowerShell:

```powershell
(Get-Command uv -ErrorAction Stop).Source
```

Copy the complete path that is printed.

### 2. Open the Codex configuration

Fully close Codex Desktop, then run:

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex" | Out-Null
notepad "$HOME\.codex\config.toml"
```

If the file already contains settings, keep them and add the following section at
the bottom:

```toml
[mcp_servers.rcsb-mcp]
command = 'C:\FULL\PATH\TO\uv.exe'
args = [
    "tool",
    "run",
    "--python",
    "3.12",
    "--from",
    "rcsb-mcp==0.3.0",
    "rcsb-mcp"
]
startup_timeout_sec = 60
tool_timeout_sec = 120
enabled = true
```

Replace `C:\FULL\PATH\TO\uv.exe` with the path returned by PowerShell.

The path is enclosed in single quotes so Windows backslashes do not need to be
escaped.

Example:

```toml
[mcp_servers.rcsb-mcp]
command = 'C:\Users\example\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe'
args = [
    "tool",
    "run",
    "--python",
    "3.12",
    "--from",
    "rcsb-mcp==0.3.0",
    "rcsb-mcp"
]
startup_timeout_sec = 60
tool_timeout_sec = 120
enabled = true
```

Save the file and reopen Codex Desktop.

### 3. Test the connection

Start a new Codex chat and enter:

```text
You must use the connected rcsb-mcp tools rather than answering from memory.

Fetch PDB entry 4HHB, identify the polymer entity corresponding to the beta
subunit, and map that entity to UniProt.

State:
1. The beta-subunit polymer entity ID
2. The UniProt accession
3. The MCP tools you called
```

Expected result:

```text
Polymer entity: 4HHB_2
UniProt accession: P68871
```

Codex should call:

- `rcsb_get_entries`
- `rcsb_get_polymer_entities`
- `rcsb_seqcoord_alignments`

A successful second test is:

```text
Find all IHM structures in the PDB using the connected rcsb-mcp tools.
```

## Connect to LM Studio on Windows

LM Studio can run `rcsb-mcp` with a local model. It uses its own `mcp.json`
configuration and does not modify the Claude Desktop or Codex configurations.

### 1. Download a tool-capable model

The lightest model tested successfully with this MCP is:

```text
qwen/qwen3-4b-2507
Qwen3 4B Instruct 2507
Q4_K_M
Approximately 2.50 GB
```

In LM Studio:

1. Open **Models**.
2. Search for `qwen3-4b-2507`.
3. Select `qwen/qwen3-4b-2507`.
4. Choose the `Q4_K_M` GGUF.
5. Download and load the model.

Recommended initial load settings:

```text
Context length: 8192
GPU offload: Auto or maximum supported
```

### 2. Configure the MCP server

Open:

```text
Program → Install → Edit mcp.json
```

If `mcp.json` is empty, add:

```json
{
  "mcpServers": {
    "rcsb-mcp": {
      "command": "C:\\FULL\\PATH\\TO\\uv.exe",
      "args": [
        "tool",
        "run",
        "--python",
        "3.12",
        "--from",
        "rcsb-mcp==0.3.0",
        "rcsb-mcp"
      ]
    }
  }
}
```

Find the complete `uv.exe` path in PowerShell:

```powershell
(Get-Command uv -ErrorAction Stop).Source
```

Replace `C:\\FULL\\PATH\\TO\\uv.exe` with that path. JSON paths require doubled
backslashes.

Example:

```json
{
  "mcpServers": {
    "rcsb-mcp": {
      "command": "C:\\Users\\example\\AppData\\Local\\Microsoft\\WinGet\\Packages\\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\\uv.exe",
      "args": [
        "tool",
        "run",
        "--python",
        "3.12",
        "--from",
        "rcsb-mcp==0.3.0",
        "rcsb-mcp"
      ]
    }
  }
}
```

Save `mcp.json`. In the **Program** panel, confirm that:

- `mcp/rcsb-mcp` is enabled;
- the `rcsb_*` tools are visible;
- the `rcsb-mcp` integration is attached to the chat.

No local repository folder needs to be opened when using the published package.

### 3. Limit the enabled tools for small models

`rcsb-mcp` exposes a large tool catalog with detailed schemas. A 4B model may
fail, return an empty response, or produce an invalid tool call when every tool
is enabled at once.

For best results with Qwen3 4B:

- start a new chat for each task;
- enable only the tools needed for that task;
- state the tool names and steps explicitly;
- avoid requesting very large result sets unless necessary.

For the 4HHB test, enable only:

```text
rcsb_get_entries
rcsb_get_polymer_entities
rcsb_seqcoord_alignments
```

Then enter:

```text
Use the connected RCSB tools.

1. Call rcsb_get_entries for 4HHB.
2. Call rcsb_get_polymer_entities for 4HHB_1 and 4HHB_2.
3. Identify the beta subunit.
4. Call rcsb_seqcoord_alignments to map that entity from PDB_ENTITY to UNIPROT.

Return:
1. The beta-subunit polymer entity ID
2. The UniProt accession
3. The tools called
```

Expected result:

```text
Polymer entity: 4HHB_2
UniProt accession: P68871
```

### 4. Test an IHM search

Start a new chat and enable only:

```text
rcsb_search_by_attribute
```

Enter:

```text
Call rcsb_search_by_attribute with:

attributes:
- attribute: rcsb_entry_info.structure_determination_methodology
  operator: exact_match
  value: integrative

return_type: entry
limit: 1
all_hits: false
enrich: false

Report:
1. total_count
2. the exact attribute and value used
3. the tool called
```

At the time this setup was tested, the result was:

```text
total_count: 391
attribute: rcsb_entry_info.structure_determination_methodology
value: integrative
tool: rcsb_search_by_attribute
```

The number of matching PDB entries may increase over time.

### Troubleshooting

#### The model returns no content

Start a new chat and enable fewer tools. The visible chat may be empty while MCP
instructions and tool schemas still consume model context.

#### The model fails to generate a tool call

Enable only the required tools and explicitly state which tool should be called
and which arguments it should receive.

#### The model fails to load

Return to conservative settings:

```text
Context length: 8192
GPU offload: Auto
```

Higher context settings can require significantly more memory.

#### Context usage exceeds 100%

LM Studio may truncate the prompt to fit the loaded context. A simple, explicit
single-tool request can still work, but multi-tool workflows become unreliable.

Qwen3 4B Q4_K_M is the lightest model tested successfully with `rcsb-mcp`.
A larger tool-capable model is recommended when using the complete tool catalog
without manually limiting the enabled tools.

## Other model options

`rcsb-mcp` can work with any MCP-capable client and a model that can reliably
call tools. A normal web-chat subscription does not automatically mean MCP is
supported.

### Gemini

Consumer Gemini CLI access ended on June 18, 2026. For free individual use, use
Google Antigravity instead.

* Antigravity supports local MCP servers.
* The individual plan can be used with eligible personal Google accounts.
* Google AI Pro is not required.
* Workspace or university accounts may not qualify.

Gemini CLI may still work through organizational Gemini Code Assist access or a
Gemini API key.

### Qwen

Qwen can use `rcsb-mcp` through MCP-capable clients such as Qwen Code or
LM Studio.

Remote Qwen models usually require Alibaba ModelStudio, an API key, or another
supported provider. The free Qwen OAuth tier ended on April 15, 2026.

Open-weight Qwen models can also run locally in LM Studio without an API key.

### DeepSeek

Hosted DeepSeek usually requires a DeepSeek API key or another MCP-capable
provider that offers DeepSeek models.

The regular DeepSeek website or mobile app is not an MCP client.

Open-weight DeepSeek models can also run locally in LM Studio without an API key.
