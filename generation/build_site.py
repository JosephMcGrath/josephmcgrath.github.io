# -*- coding: utf-8 -*-

import os
import jinja2
import markdown
import re
import datetime


class simple_markdown:
    """Converts a markdown file into html with attached metadata."""

    markdown_extensions = ["fenced_code", "meta"]

    def __init__(self, src_path):
        self.parse_markdown(src_path)

    def parse_markdown(self, src_path):
        """
        Converts a markdown file to html (results stored on the simple_markdown
        object rather than returned).
        """
        markdown_parser = markdown.Markdown(extensions=self.markdown_extensions)

        with open(src_path, "r") as f:
            lines_in = f.readlines()

        self.file_path = src_path
        self.markdown = "".join([x for x in lines_in if not re.match(r"^\@", x)])
        self.html = markdown_parser.convert(self.markdown)
        self.meta = markdown_parser.Meta

        if "finished" in self.meta:
                self.finished = self.meta.get("finished")[0] == "True"
        else:
            False
        self.title = self.meta.get("title")[0]

    def metadata(self):
        """Consolidates metadata entries to strings."""
        output = {key: ",".join(self.meta[key]) for key in self.meta}

        return output


class site_press:
    def __init__(self, root_dir, css_style=None):
        self.root_dir = root_dir
        self.css_style = css_style

        file_loader = jinja2.FileSystemLoader(os.path.join(root_dir, "templates"))
        self.env = jinja2.Environment(loader=file_loader)

    def make_index(self):
        """Generates the site index / home page."""
        template = self.env.get_template("page.html")
        body = self.env.get_template("index.html")

        page_title = "Joe McGrath"

        metadata = {
            "title": page_title,
            "description": "Joe McGrath's personal site.",
            "date_generated": datetime.datetime.now().isoformat(),
        }

        index_page = template.render(
            metadata=metadata,
            title=page_title,
            style=self.css_style,
            body=body.render(),
        )

        with open(os.path.join(self.root_dir, "index.html"), "w") as f:
            f.writelines(index_page)

    def webify(self, string):
        """Converts a string into one suitable for a url."""
        string = string.lower()
        string = string.replace("_", "-")
        string = re.sub(r"\s|\_", "-", string)
        return string

    def blog_path(self, src_path, dir_out="blog"):
        """Alters a markdown file path to be under the blog directory (on disc)."""
        file_name = self.blog_name(src_path)
        file_name = os.path.splitext(file_name)[0] + ".html"

        file_out = os.path.join(self.root_dir, dir_out, file_name)
        return file_out

    def blog_name(self, src_path):
        """Extracts a blog name from a file path."""
        file_name = self.webify(os.path.split(src_path)[-1])
        file_name = os.path.splitext(file_name)[0]
        return file_name

    def render_blog(self, src_file):
        """Renders a single markdown blog to a html file."""
        file_out = self.blog_path(src_file)
        template = self.env.get_template("page.html")

        blog_in = simple_markdown(src_file)

        if blog_in.finished:
            page_out = template.render(
                title=blog_in.title,
                style=self.css_style,
                body=blog_in.html,
                metadata=blog_in.metadata(),
            )
            with open(file_out, "w") as f:
                f.writelines(page_out)

        return blog_in

    def render_all_blogs(self):
        """Renders all finished blogs and create the blog list."""
        page = self.env.get_template("page.html")
        b_list = self.env.get_template("blog_list.html")
        search_dir = os.path.join(self.root_dir, "markdown")
        all_files = os.listdir(search_dir)
        all_files = [x for x in all_files if re.match(r".*\.md$", x)]
        all_files = [os.path.join(search_dir, x) for x in all_files]

        self.blog_list = []
        for this_blog in all_files:
            temp = self.render_blog(this_blog)
            if temp.finished:
                self.blog_list.append(temp)

        for this_blog in self.blog_list:
            this_blog.url = self.blog_name(this_blog.file_path)

        page_out = page.render(
            title="Blogs",
            style=self.css_style,
            body=b_list.render(blogs=self.blog_list),
        )

        with open(self.blog_path("blogs"), "w") as f:
            f.writelines(page_out)


site = site_press(os.path.dirname(os.getcwd()), "/main.css")
site.make_index()
site.render_all_blogs()
