from pathlib import Path

import pytest

from nikola.jekyll_import import parse_post, parse_posts


POSTS_DIR = Path(__file__).parent / "data" / "jekyll_import" / "_posts"


def test_parse_regular_post():
    post = parse_post(POSTS_DIR / "2024-03-10-first-post.md")

    assert post["title"] == "First post"
    assert post["slug"] == "first-post"
    assert post["tags"] == ["demo"]
    assert post["content"] == "This is the first example post.\n"
    assert post["permalink"] is None
    assert post["old_url"] == "/2024/03/10/first-post.html"
    assert post["new_url"] == "/posts/first-post.html"


def test_parse_post_with_custom_permalink():
    post = parse_post(POSTS_DIR / "2024-03-11-custom-url.md")

    assert post["title"] == "Custom URL post"
    assert post["slug"] == "custom-url-post"
    assert post["tags"] == ["demo"]
    assert post["permalink"] == "/special/custom-post/"
    assert post["content"] == "This post has a custom old URL.\n"
    assert post["old_url"] == "/special/custom-post/"
    assert post["new_url"] == "/posts/custom-url-post.html"


def test_parse_posts_returns_url_mappings():
    posts = parse_posts(POSTS_DIR)

    assert [(post["old_url"], post["new_url"]) for post in posts] == [
        ("/2024/03/10/first-post.html", "/posts/first-post.html"),
        ("/special/custom-post/", "/posts/custom-url-post.html"),
    ]


@pytest.mark.parametrize("field", ["title", "date", "slug"])
def test_missing_required_metadata(tmp_path, field):
    fields = {
        "title": "Post",
        "date": "2024-03-10",
        "slug": "post",
    }
    del fields[field]
    front_matter = "".join(f"{key}: {value}\n" for key, value in fields.items())
    post_path = tmp_path / "post.md"
    post_path.write_text(f"---\n{front_matter}---\nBody\n", encoding="utf-8")

    with pytest.raises(ValueError, match=f"Missing {field}"):
        parse_post(post_path)


def test_invalid_front_matter(tmp_path):
    post_path = tmp_path / "post.md"
    post_path.write_text("---\ntitle: Post\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Front matter must be closed"):
        parse_post(post_path)


def test_invalid_date(tmp_path):
    post_path = tmp_path / "post.md"
    post_path.write_text(
        "---\ntitle: Post\ndate: not-a-date\nslug: post\n---\nBody\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid date"):
        parse_post(post_path)


def test_permalink_must_be_path_only(tmp_path):
    post_path = tmp_path / "post.md"
    post_path.write_text(
        "---\ntitle: Post\ndate: 2024-03-10\nslug: post\n"
        "permalink: https://example.com/post/\n---\nBody\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Permalink must be a path"):
        parse_post(post_path)


def test_parse_posts_rejects_duplicate_old_urls(tmp_path):
    first = tmp_path / "2024-03-10-first.md"
    second = tmp_path / "2024-03-11-second.md"
    first.write_text(
        "---\ntitle: First\ndate: 2024-03-10\nslug: first\npermalink: /same/\n---\n",
        encoding="utf-8",
    )
    second.write_text(
        "---\ntitle: Second\ndate: 2024-03-11\nslug: second\npermalink: /same/\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate old URL: /same/"):
        parse_posts(tmp_path)
