from pathlib import Path

import pytest

from nikola.hugo_import import parse_post, parse_posts


POSTS_DIR = Path(__file__).parent / "data" / "hugo_import" / "content" / "posts"


def test_parse_regular_post():
    post = parse_post(POSTS_DIR / "first-post.md")

    assert post["title"] == "First post"
    assert post["slug"] == "first-post"
    assert post["tags"] == ["demo"]
    assert post["content"] == "This is the first example post.\n"
    assert post["url"] is None
    assert post["old_url"] == "/posts/first-post/"
    assert post["new_url"] == "/posts/first-post.html"


def test_parse_post_with_custom_url():
    post = parse_post(POSTS_DIR / "custom-url-post.md")

    assert post["title"] == "Custom URL post"
    assert post["slug"] == "custom-url-post"
    assert post["url"] == "/special/custom-post/"
    assert post["old_url"] == "/special/custom-post/"
    assert post["new_url"] == "/posts/custom-url-post.html"


def test_parse_posts_returns_url_mappings():
    posts = parse_posts(POSTS_DIR)

    assert [(post["old_url"], post["new_url"]) for post in posts] == [
        ("/special/custom-post/", "/posts/custom-url-post.html"),
        ("/posts/first-post/", "/posts/first-post.html"),
    ]


def test_slug_from_filename(tmp_path):
    post_path = tmp_path / "hello-world.md"
    post_path.write_text(
        "---\ntitle: Hello\ndate: 2024-03-10\n---\nBody\n",
        encoding="utf-8",
    )
    post = parse_post(post_path)
    assert post["slug"] == "hello-world"
    assert post["old_url"] == "/posts/hello-world/"


@pytest.mark.parametrize("field", ["title", "date"])
def test_missing_required_metadata(tmp_path, field):
    fields = {
        "title": "Post",
        "date": "2024-03-10",
    }
    del fields[field]
    front_matter = "".join(f"{key}: {value}\n" for key, value in fields.items())
    post_path = tmp_path / "post.md"
    post_path.write_text(f"---\n{front_matter}---\nBody\n", encoding="utf-8")

    with pytest.raises(ValueError, match=f"Missing {field}"):
        parse_post(post_path)
