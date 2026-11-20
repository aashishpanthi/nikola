"""Parse the supported Hugo post subset into records for the importer.

Call ``parse_posts("/path/to/hugo/content/posts")``. It reads direct-child
``*.md`` files with ``title`` and ``date``, optional ``slug`` (else the
filename stem), optional ``tags``, and an optional path ``url``. Each returned
record contains ``source_path``, ``content``, ``title``, ``date``, ``slug``,
``tags``, ``url``, ``old_url``, and ``new_url``.

``old_url`` is the explicit ``url`` or ``/posts/{slug}/``; ``new_url`` is
``/posts/{slug}.html``. URLs are path-only, and duplicate ``old_url`` values
raise ``ValueError``.

This is a deliberately small demo parser. It does not process config files,
page bundles, shortcodes, TOML/JSON front matter, multilingual sites,
non-Markdown posts, or assets.
"""

from pathlib import Path
from urllib.parse import urlsplit

from nikola.jekyll_import import _parse_front_matter


def parse_post(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    meta, body = _parse_front_matter(text)
    body = body.strip("\n")

    title = meta.get("title", "")
    date = meta.get("date", "")
    slug = meta.get("slug") or path.stem
    tags = meta.get("tags", [])
    url = meta.get("url")

    if not title:
        raise ValueError(f"Missing title in {path}")
    if not date:
        raise ValueError(f"Missing date in {path}")

    if url:
        parsed_url = urlsplit(url)
        if any([parsed_url.scheme, parsed_url.netloc, parsed_url.query,
                parsed_url.fragment, "?" in url, "#" in url, not parsed_url.path]):
            raise ValueError(f"url must be a path without query or fragment in {path}")
        old_url = "/" + parsed_url.path.lstrip("/")
    else:
        old_url = f"/posts/{slug}/"

    return {
        "source_path": str(path),
        "title": title,
        "date": date,
        "slug": slug,
        "tags": tags,
        "url": url,
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
