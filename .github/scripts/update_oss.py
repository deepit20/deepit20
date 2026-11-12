"""Rebuild the open source table in README.md from GitHub's search API.

Lists pull requests authored by the profile owner in repositories they do not
own: merged ones first (newest first), then ones still open.
"""
import json
import os
import re
import urllib.parse
import urllib.request

USER = os.environ.get("GH_USER", "deepit20")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
START, END = "<!-- OSS:START -->", "<!-- OSS:END -->"


def search(query):
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
        {"q": query, "sort": "created", "order": "desc", "per_page": 50}
    )
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data["items"], data["total_count"]


def row(pr, status):
    repo = pr["repository_url"].split("/repos/")[1]
    title = pr["title"].replace("|", "\|")
    return (f"| [**{repo}**](https://github.com/{repo}) "
            f"| [#{pr['number']}]({pr['html_url']}): {title} | {status} |")


merged, merged_total = search(f"is:pr author:{USER} is:merged -user:{USER}")
opened, _ = search(f"is:pr author:{USER} is:open -user:{USER}")
lines = ["| Project | Contribution | Status |", "|---|---|---|"]
lines += [row(p, "✅ Merged") for p in merged]
lines += [row(p, "🟡 In review") for p in opened]
if len(lines) == 2:
    lines.append("| | First contribution coming soon | |")
count = f"**{merged_total} merged pull request{'s' if merged_total != 1 else ''}** to other projects"
block = f"{START}\n{count}\n\n" + "\n".join(lines) + f"\n\n<sub>Updated automatically every day.</sub>\n{END}"

with open("README.md", encoding="utf-8") as f:
    text = f.read()
if START not in text or END not in text:
    raise SystemExit("OSS markers not found in README.md")
new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
if new != text:
    with open("README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    print("README updated")
else:
    print("no change")
