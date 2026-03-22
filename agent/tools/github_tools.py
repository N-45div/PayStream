"""GitHub PR monitoring tools for LangChain agent."""

from __future__ import annotations
import httpx
from langchain_core.tools import tool

from core.config import GITHUB_TOKEN, GITHUB_REPO


@tool
def get_merged_prs(repo: str = "", limit: int = 10) -> list[dict]:
    """Fetch recently merged pull requests from a GitHub repository.
    Returns PR number, title, author, additions, deletions, changed_files, merged_at, labels, url."""
    target = repo or GITHUB_REPO
    if not target:
        return [{"error": "No repo configured. Set GITHUB_REPO env var or pass repo arg."}]

    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    url = f"https://api.github.com/repos/{target}/pulls"
    params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": min(limit, 30)}

    resp = httpx.get(url, headers=headers, params=params, timeout=15)
    if resp.status_code != 200:
        return [{"error": f"GitHub API {resp.status_code}: {resp.text[:200]}"}]

    results = []
    for pr in resp.json():
        if not pr.get("merged_at"):
            continue
        results.append({
            "number": pr["number"],
            "title": pr["title"],
            "author": pr["user"]["login"],
            "body": (pr.get("body") or "")[:300],
            "merged_at": pr["merged_at"],
            "merged_by": (pr.get("merged_by") or {}).get("login", "unknown"),
            "labels": [l["name"] for l in pr.get("labels", [])],
            "url": pr["html_url"],
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changed_files", 0),
        })
    return results[:limit]


@tool
def get_pr_details(repo: str, pr_number: int) -> dict:
    """Get detailed stats for a specific pull request including additions, deletions, changed files."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    resp = httpx.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return {"error": f"GitHub API {resp.status_code}"}

    pr = resp.json()
    return {
        "number": pr["number"],
        "title": pr["title"],
        "author": pr["user"]["login"],
        "body": (pr.get("body") or "")[:500],
        "state": pr["state"],
        "merged": pr.get("merged", False),
        "merged_at": pr.get("merged_at"),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "changed_files": pr.get("changed_files", 0),
        "labels": [l["name"] for l in pr.get("labels", [])],
        "url": pr["html_url"],
    }
