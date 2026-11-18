"""
Testing the Hugo import.

It will create a new site with the import_hugo command
and use that newly created site to make a build.
"""

import csv
import os.path

import pytest

from nikola import __main__
from nikola.plugins.command.import_hugo import redirect_source

from .helper import cd
from .test_empty_build import (  # NOQA
    test_check_files,
)


def test_import_created_files(build, target_dir):
    assert os.path.exists(os.path.join(target_dir, "conf.py"))
    assert os.path.exists(os.path.join(target_dir, "url_map.csv"))


def test_redirects_and_posts(build, target_dir, output_dir):
    with open(os.path.join(target_dir, "url_map.csv"), newline="") as fd:
        for old_url, new_url in csv.reader(fd):
            new_path = os.path.join(output_dir, new_url.lstrip("/"))
            assert os.path.isfile(new_path), new_path
            src = redirect_source(old_url)
            assert src is not None, old_url
            redirect_path = os.path.join(output_dir, src)
            assert os.path.isfile(redirect_path), redirect_path


@pytest.fixture(scope="module")
def build(target_dir, hugo_site):
    __main__.main(
        [
            "import_hugo",
            "--output-folder",
            target_dir,
            hugo_site,
        ]
    )

    with cd(target_dir):
        result = __main__.main(["build"])
        assert not result


@pytest.fixture(scope="module")
def hugo_site(test_dir):
    """Path to the fixture Hugo site."""
    return os.path.join(test_dir, "..", "data", "hugo_import")
