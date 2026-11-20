import pytest

from nikola.plugins.command.import_jekyll import redirect_source


@pytest.mark.parametrize(
    "old_url, expected",
    [
        ("/2024/03/10/first-post.html", "2024/03/10/first-post.html"),
        ("/special/custom-post/", "special/custom-post/index.html"),
        ("/about", None),
    ],
)
def test_redirect_source(old_url, expected):
    assert redirect_source(old_url) == expected
