#!/usr/bin/env python3
"""
cleanup_branches.py - Automatic cleanup of merged git branches on GitHub.
Uses GITHUB_RELEASE_TOKEN from .env file and deletes all branches that are
already merged into main/master.
"""

import os
import re
import sys
import subprocess
import urllib.request
import urllib.error


def run_cmd(args, cwd=None):
    try:
        res = subprocess.run(args, capture_output=True, text=True, check=True, cwd=cwd)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command {' '.join(args)}: {e.stderr.strip()}", file=sys.stderr)
        return ""


def load_env(env_path):
    env = {}
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_repo_details(cwd):
    remote_url = run_cmd(["git", "remote", "get-url", "origin"], cwd=cwd)
    if not remote_url:
        print("Failed to retrieve remote repository URL.", file=sys.stderr)
        return None, None

    # Matches https://github.com/owner/repo(.git) or git@github.com:owner/repo(.git)
    match = re.search(r"github\.com[:/]([^/]+)/([^.]+)(?:\.git)?", remote_url)
    if not match:
        print(f"Unsupported repository URL format: {remote_url}", file=sys.stderr)
        return None, None

    return match.group(1), match.group(2)


def get_merged_branches_from_github_api(owner, repo, token):
    import json

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=closed&per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Antigravity-Cleanup-Tool",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            prs = json.loads(resp.read().decode())
            merged_branches = set()
            for pr in prs:
                if pr.get("merged_at") and pr.get("head") and pr["head"].get("ref"):
                    merged_branches.add(pr["head"]["ref"])
            return merged_branches
    except Exception as e:
        print(f"Warning: Failed to load merged PRs via API: {e}", file=sys.stderr)
        return set()


def main():
    cwd = os.getcwd()
    git_root = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    if not git_root:
        print("Error: You are not inside a Git repository.", file=sys.stderr)
        sys.exit(1)

    env = {}
    env_paths = [os.path.join(git_root, ".env"), "/root/geminicli/.env"]
    for path in env_paths:
        if os.path.exists(path):
            env.update(load_env(path))

    token = env.get("GITHUB_RELEASE_TOKEN") or os.environ.get("GITHUB_RELEASE_TOKEN")
    if not token:
        print(
            "Error: GITHUB_RELEASE_TOKEN not found in .env file or environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo = get_repo_details(git_root)
    if not owner or not repo:
        sys.exit(1)

    print(f"🔍 [Antigravity Custom] Analyzing repository {owner}/{repo}...")
    run_cmd(["git", "fetch", "origin", "--prune"], cwd=git_root)

    # Determine default branch (main or master)
    default_branch = "main"
    all_remote_branches_raw = run_cmd(["git", "branch", "-r"], cwd=git_root)
    if "origin/master" in all_remote_branches_raw and "origin/main" not in all_remote_branches_raw:
        default_branch = "master"

    merged_output = run_cmd(
        ["git", "branch", "-r", "--merged", f"origin/{default_branch}"], cwd=git_root
    )
    github_merged = get_merged_branches_from_github_api(owner, repo, token)

    protected_branches = {"main", "master", "dev", "development", "stable", "HEAD"}
    branches_to_delete = []

    # Retrieve unique remote branches
    for line in all_remote_branches_raw.split("\n"):
        line = line.strip()
        if not line or "->" in line:
            continue
        branch_name = line.replace("origin/", "", 1)
        if branch_name in protected_branches:
            continue

        # A branch is considered merged if:
        # 1. Marked as merged in local git
        # 2. Or is among merged PRs on GitHub (squash merge)
        is_merged_local = line in merged_output.split("\n") or line.strip() in [
            l.strip() for l in merged_output.split("\n")
        ]
        is_merged_github = branch_name in github_merged

        if is_merged_local or is_merged_github:
            if branch_name not in branches_to_delete:
                branches_to_delete.append(branch_name)

    if not branches_to_delete:
        print("✨ All merged branches have already been deleted!")
        return

    print(f"Found {len(branches_to_delete)} merged branches to delete:")
    for b in branches_to_delete:
        print(f" - {b}")

    deleted_count = 0
    for branch in branches_to_delete:
        print(f"🗑️ Deleting {branch} from GitHub...")
        url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
        req = urllib.request.Request(
            url,
            method="DELETE",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Antigravity-Cleanup-Tool",
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status in (200, 204):
                    print(f"✅ Branch {branch} successfully deleted from GitHub.")
                    deleted_count += 1
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                print(f"ℹ️ Branch {branch} not found on GitHub (may have already been deleted).")
                deleted_count += 1
            else:
                print(
                    f"❌ Failed to delete branch {branch}: HTTP {e.code} - {e.reason}",
                    file=sys.stderr,
                )
        except Exception as e:
            print(f"❌ Error deleting branch {branch}: {e}", file=sys.stderr)

    if deleted_count > 0:
        run_cmd(["git", "fetch", "origin", "--prune"], cwd=git_root)
        print(f"🎉 Process complete. Deleted {deleted_count} branches.")
    else:
        print("No branches were deleted.")


if __name__ == "__main__":
    main()
