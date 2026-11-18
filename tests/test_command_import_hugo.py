import pytest

from nikola.plugins.command.import_hugo import redirect_source


@pytest.mark.parametrize(
    "old_url, expected",
    [
        ("/posts/first-post/", "posts/first-post/index.html"),
        ("/special/custom-post/", "special/custom-post/index.html"),
        ("/about", None),
    ],
)
def test_redirect_source(old_url, expected):
    assert redirect_source(old_url) == expected
