"""Parse the supported Jekyll post subset into records for the importer.

Call ``parse_posts("/path/to/jekyll/_posts")``. It reads direct-child ``*.md``
files with ``title``, ``date``, and ``slug`` fields, optional ``tags``, and an
optional literal path ``permalink``. Each returned record contains
``source_path``, ``content``, ``title``, ``date``, ``slug``, ``tags``,
``permalink``, ``old_url``, and ``new_url``.

``old_url`` is the explicit permalink or ``/{YYYY}/{MM}/{DD}/{slug}.html``;
``new_url`` is ``/posts/{slug}.html``. URLs are path-only, and duplicate
``old_url`` values raise ``ValueError``.

This is a deliberately small demo parser, not a general Jekyll or YAML
implementation. It does not process themes, plugins, arbitrary front matter,
comments, shortcodes, non-Markdown posts, or assets.
"""

from datetime import date as Date
from pathlib import Path
import re
from urllib.parse import urlsplit


def _parse_front_matter(text):
    if not text.startswith("---\n"):
        raise ValueError("Missing YAML front matter")

    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError("Front matter must be closed with ---")

    front = parts[0][4:]
    body = parts[1]

    data = {}
    in_tags = False
    tag_values = []

    lines = front.splitlines()
    for line in lines:
        if not line.strip():
            continue

        if line.startswith("tags:"):
            # tags: [a, b] or tags: followed by list items
            value = line.split(":", 1)[1].strip()
            if value:
                if value.startswith("[") and value.endswith("]"):
                    data["tags"] = [x.strip().strip("'\"") for x in value[1:-1].split(",") if x.strip()]
                else:
                    data["tags"] = []
                    tag_values = []
                    in_tags = True
                    if value:
                        tag_values.append(value.strip().strip("'\""))
            else:
                data["tags"] = []
                in_tags = True
            continue

        if in_tags:
            if line.startswith("  - "):
                tag_values.append(line.split("-", 1)[1].strip().strip("'\""))
                continue
            if line.startswith("  ") and not line.startswith("  - "):
                # end of tag block
                in_tags = False

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value.strip("'\"")
            else:
                data[key] = ""
        else:
            # ignore weird lines
            pass

    if in_tags and tag_values:
        data["tags"] = tag_values

    if "tags" not in data:
        data["tags"] = []

    return data, body


def parse_post(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    meta, body = _parse_front_matter(text)
    body = body.strip("\n")

    title = meta.get("title", "")
    date = meta.get("date", "")
    slug = meta.get("slug", "")
    tags = meta.get("tags", [])
    permalink = meta.get("permalink")

    if not title:
        raise ValueError(f"Missing title in {path}")
    if not date:
        raise ValueError(f"Missing date in {path}")
    if not slug:
        raise ValueError(f"Missing slug in {path}")

    try:
        post_date = Date.fromisoformat(date[:10])
    except ValueError as error:
        raise ValueError(f"Invalid date in {path}: {date}") from error

    if permalink:
        parsed_permalink = urlsplit(permalink)
        if (
            parsed_permalink.scheme
            or parsed_permalink.netloc
            or parsed_permalink.query
            or parsed_permalink.fragment
            or "?" in permalink
            or "#" in permalink
            or not parsed_permalink.path
        ):
            raise ValueError(f"Permalink must be a path without query or fragment in {path}")
        old_url = "/" + parsed_permalink.path.lstrip("/")
    else:
        old_url = f"/{post_date:%Y/%m/%d}/{slug}.html"

    return {
        "source_path": str(path),
        "title": title,
        "date": date,
        "slug": slug,
        "tags": tags,
        "permalink": permalink,
        "old_url": old_url,
        "new_url": f"/posts/{slug}.html",
        "content": body + ("\n" if body and not body.endswith("\n") else ""),
    }


def parse_posts(directory):
    directory = Path(directory)
    posts = [parse_post(p) for p in sorted(directory.glob("*.md"))]
    urls = set()
    for post in posts:
        if post["old_url"] in urls:
            raise ValueError(f"Duplicate old URL: {post['old_url']}")
        urls.add(post["old_url"])
    return posts
