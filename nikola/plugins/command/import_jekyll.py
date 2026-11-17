"""Import Markdown posts from a small Jekyll site into a new Nikola site."""

import os

from nikola.jekyll_import import parse_posts
from nikola.plugin_categories import Command
from nikola.plugins.basic_import import ImportMixin
from nikola.plugins.command.init import SAMPLE_CONF, prepare_config
from nikola.utils import LOGGER


def redirect_source(old_url):
    """Return the path inside output/ where the redirect page for old_url goes, or None."""
    path = old_url.lstrip("/")
    if path.endswith(".html"):
        return path
    if path.endswith("/"):
        return path + "index.html"
    return None


class CommandImportJekyll(Command, ImportMixin):
    """Import Markdown posts from a Jekyll site, with redirects from the old URLs."""

    name = "import_jekyll"
    needs_config = False
    doc_usage = "[options] jekyll_site_folder"
    doc_purpose = "import a small Jekyll site"
    cmd_options = ImportMixin.cmd_options

    def _execute(self, options={}, args=[]):
        if not args:
            print(self.help())
            return False
        jekyll_root = args[0]
        self.output_folder = options.get("output_folder", "new_site")
        self.import_into_existing_site = False

        records = parse_posts(os.path.join(jekyll_root, "_posts"))
        seen = {}
        for r in records:
            if r["new_url"] in seen:
                LOGGER.error("{0} and {1} would both become {2}".format(
                    seen[r["new_url"]], r["source_path"], r["new_url"]))
                return False
            seen[r["new_url"]] = r["source_path"]

        conf_template = self.generate_base_site()
        url_map = {}
        redirections = []
        for r in records:
            base = os.path.join(self.output_folder, "posts", r["slug"])
            self.write_metadata(base + ".meta", r["title"], r["slug"], r["date"], "", r["tags"])
            self.write_content(base + ".md", r["content"], rewrite_html=False)
            url_map[r["old_url"]] = r["new_url"]
            src = redirect_source(r["old_url"])
            if src is None:
                LOGGER.warning("No redirect for {0}: it must end in .html or /".format(r["old_url"]))
            else:
                redirections.append((src, r["new_url"]))

        context = SAMPLE_CONF.copy()
        context["PRETTY_URLS"] = False
        context["REDIRECTIONS"] = redirections
        self.write_urlmap_csv(os.path.join(self.output_folder, "url_map.csv"), url_map)
        self.write_configuration(self.get_configuration_output_path(),
                                 conf_template.render(**prepare_config(context)))
        LOGGER.info("Imported {0} posts into {1}".format(len(records), self.output_folder))
