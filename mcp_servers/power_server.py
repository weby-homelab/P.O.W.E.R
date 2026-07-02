#!/usr/bin/env python3
import asyncio
import os
import sys
import re
from pathlib import Path
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("power")

def get_vault_path(arguments: dict) -> Path:
    val = arguments.get("vault_path")
    if val:
        return Path(val).resolve()
    
    env_val = os.getenv("POWER_VAULT_DIR")
    if env_val:
        return Path(env_val).resolve()
        
    return Path(os.getcwd()).resolve()

# 1. Self-contained Index Generator
def run_generate_index(vault_dir: Path) -> str:
    index_path = vault_dir / "index.md"
    log_path = vault_dir / "log.md"
    
    concepts = {}
    
    def parse_metadata(filepath):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
        if not match:
            return None
        yaml_content = match.group(1)
        meta = {}
        for line in yaml_content.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip().strip('"').strip("'")
        return meta

    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in [".git", "05_Templates", "scratch", ".system_generated", ".agents"]]
        for file in files:
            if file.endswith(".md") and file not in ["index.md", "log.md"]:
                filepath = Path(root) / file
                try:
                    meta = parse_metadata(filepath)
                    if meta:
                        m_type = meta.get("type", "Resource")
                        rel_path = os.path.relpath(filepath, vault_dir)
                        title = meta.get("title", file)
                        desc = meta.get("description", "")
                        
                        if m_type not in concepts:
                            concepts[m_type] = []
                        concepts[m_type].append((rel_path, title, desc))
                except Exception:
                    pass
                    
    index_content = [
        "---",
        "type: System Guide",
        'title: "Second Brain Index"',
        'description: "Registry of all concepts in the Second Brain"',
        f"timestamp: {datetime.now().isoformat()}",
        "---",
        "\n# 🗂️ Knowledge Catalog (OKF Index)\n",
        "Цей файл автоматично підтримується в актуальному стані ШІ-агентами та містить перелік усіх сторінок бази знань, класифікованих за типами.\n"
    ]
    
    defined_order = ["System Guide", "Project", "Area", "Resource", "Daily Log", "Archive"]
    sorted_types = sorted(concepts.keys(), key=lambda t: defined_order.index(t) if t in defined_order else 99)
    
    for m_type in sorted_types:
        index_content.append(f"## 📁 {m_type}s")
        items = sorted(concepts[m_type], key=lambda x: x[1])
        for rel_path, title, desc in items:
            index_content.append(f"- **[{title}]({rel_path})** — {desc}")
        index_content.append("")
        
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_content))
        
    total_notes = sum(len(v) for v in concepts.values())
    return f"Generated index.md with {total_notes} concepts at {index_path}."

# 2. Self-contained Linter
def run_lint_vault(vault_dir: Path) -> str:
    exclude_dirs = [".git", "05_Templates", "scratch", ".system_generated", ".agents"]
    exclude_orphan_files = [
        "README.md", "Home.md", "index.md", "log.md", 
        "Successor-Hub.md", "PARA-OKF-LLM_Wiki.md", "Weby_PARA-OKF-LLM_Wiki.md"
    ]
    
    def clean_note_name(name):
        return name.replace(".md", "").strip().lower()

    all_files = {}
    rel_paths = {}
    links = {}
    untyped_files = []
    broken_links = []
    
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(".md"):
                abs_path = Path(root) / file
                rel_path = os.path.relpath(abs_path, vault_dir)
                clean_name = clean_note_name(file)
                all_files[clean_name] = abs_path
                rel_paths[clean_name] = rel_path
                
    for clean_name, abs_path in all_files.items():
        rel_path = rel_paths[clean_name]
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
            
        has_frontmatter = content.startswith("---")
        if not has_frontmatter:
            untyped_files.append((rel_path, "No YAML frontmatter block"))
        else:
            match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
            if match:
                yaml_content = match.group(1)
                if "type:" not in yaml_content:
                    untyped_files.append((rel_path, "Missing required 'type' field"))
            else:
                untyped_files.append((rel_path, "Malformed YAML frontmatter"))
                
        wiki_links = re.findall(r"\[\[(.*?)\]\]", content)
        file_links = []
        for link in wiki_links:
            target = link.split("|")[0].split("#")[0].strip()
            if target:
                file_links.append(clean_note_name(target))
                
        gfm_links = re.findall(r"\[.*?\]\((.*?\.md)(?:#.*?)?\)", content)
        for link in gfm_links:
            target = os.path.basename(link)
            if target:
                file_links.append(clean_note_name(target))
                
        links[rel_path] = file_links
        
    for rel_path, targets in links.items():
        for target in targets:
            if target not in all_files:
                direct_file = vault_dir / f"{target}.md"
                if not direct_file.exists():
                    broken_links.append((rel_path, target))
                    
    inbound_counts = {rel_path: 0 for rel_path in links.keys()}
    for rel_path, targets in links.items():
        for target in targets:
            if target in all_files:
                target_rel_path = rel_paths[target]
                inbound_counts[target_rel_path] += 1
                
    orphans = []
    for rel_path, count in inbound_counts.items():
        filename = os.path.basename(rel_path)
        if count == 0 and filename not in exclude_orphan_files and not rel_path.startswith("06_Daily_Logs/"):
            orphans.append(rel_path)
            
    report = [
        "=== 🧹 Second Brain Health Lint Report ===",
        f"Vault scanned: {vault_dir}",
        f"Total markdown notes: {len(all_files)}\n"
    ]
    
    has_issues = False
    
    if untyped_files:
        has_issues = True
        report.append(f"⚠️  Missing/Invalid OKF Metadata ({len(untyped_files)}):")
        for rp, reason in sorted(untyped_files):
            report.append(f"  - {rp}: {reason}")
        report.append("")
        
    if broken_links:
        has_issues = True
        report.append(f"❌ Broken links found ({len(broken_links)}):")
        for rp, target in sorted(broken_links):
            report.append(f"  - In {rp}: link to [[{target}]] cannot be resolved")
        report.append("")
        
    if orphans:
        has_issues = True
        report.append(f"🕷  Orphan notes (no inbound links) ({len(orphans)}):")
        for rp in sorted(orphans):
            report.append(f"  - {rp}")
        report.append("")
        
    if not has_issues:
        report.append("✅ Vault is completely healthy! Zero errors found.")
        
    return "\n".join(report)

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="lint_vault",
            description="Run the P.O.W.E.R. health check / linter to verify note metadata, link integrity, and check for orphans.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {"type": "string", "description": "Optional absolute path to the Obsidian vault root (defaults to POWER_VAULT_DIR env var or current directory)"}
                }
            }
        ),
        Tool(
            name="generate_index",
            description="Compile the vault index.md catalog classifying all notes by their OKF metadata type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {"type": "string", "description": "Optional absolute path to the Obsidian vault root (defaults to POWER_VAULT_DIR env var or current directory)"}
                }
            }
        ),
        Tool(
            name="ingest_note",
            description="Create a new note with strict OKF metadata frontmatter, regenerate the index, and log the change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Relative path and name of the note (e.g. 01_Projects/Build-Cluster.md)"},
                    "type": {
                        "type": "string", 
                        "enum": ["Project", "Area", "Resource", "Daily Log", "Archive", "System Guide"],
                        "description": "OKF metadata type"
                    },
                    "title": {"type": "string", "description": "Human-friendly page title"},
                    "description": {"type": "string", "description": "Short, single-line description for the catalog index"},
                    "content": {"type": "string", "description": "Body content of the note"},
                    "resource": {"type": "string", "description": "Optional URL or resource link"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional list of tags"},
                    "vault_path": {"type": "string", "description": "Optional absolute path to the vault root"}
                },
                "required": ["name", "type", "title", "description", "content"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        vault_path = get_vault_path(arguments)
        
        if name == "lint_vault":
            result = run_lint_vault(vault_path)
            return [TextContent(type="text", text=result)]

        elif name == "generate_index":
            result = run_generate_index(vault_path)
            return [TextContent(type="text", text=result)]

        elif name == "ingest_note":
            note_name = arguments.get("name")
            note_type = arguments.get("type")
            title = arguments.get("title")
            description = arguments.get("description")
            content = arguments.get("content")
            resource = arguments.get("resource")
            tags = arguments.get("tags", [])

            if not note_name.endswith(".md"):
                note_name += ".md"

            target_file = vault_path / note_name

            if target_file.exists():
                return [TextContent(type="text", text=f"Error: Note already exists at {note_name}")]

            # 1. Assemble frontmatter
            timestamp = datetime.now().isoformat()
            fm_lines = [
                "---",
                f"type: {note_type}",
                f'title: "{title}"',
                f'description: "{description}"'
            ]
            if resource:
                fm_lines.append(f'resource: "{resource}"')
            if tags:
                tags_str = ", ".join(tags)
                fm_lines.append(f"tags: [{tags_str}]")
            fm_lines.append(f"timestamp: {timestamp}")
            fm_lines.append("---")
            fm_text = "\n".join(fm_lines)

            full_content = f"{fm_text}\n\n{content}\n"

            # 2. Write file
            os.makedirs(target_file.parent, exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(full_content)

            # 3. Regenerate index
            index_result = run_generate_index(vault_path)

            # 4. Log change in log.md
            log_file = vault_path / "log.md"
            if log_file.exists():
                date_str = datetime.now().strftime("%Y-%m-%d")
                log_entry = (
                    f"\n## [{date_str}] ingest | Created {title}\n"
                    f"- **Action:** Created note '{note_name}' of type {note_type} via MCP tool ingest_note.\n"
                    f"- **Result:** Saved note to {note_name} and compiled index.md.\n"
                )
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)

            # 5. Run lint check
            lint_result = run_lint_vault(vault_path)

            response_msg = (
                f"🎉 Note '{note_name}' has been successfully ingested!\n"
                f"✅ {index_result}\n"
                f"📝 Action appended to log.md.\n\n"
                f"🔍 Linting Check:\n{lint_result}"
            )
            return [TextContent(type="text", text=response_msg)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error occurred: {str(e)}")]

async def run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(run())
