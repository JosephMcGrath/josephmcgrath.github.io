# -*- coding: utf-8 -*-

import os
import jinja2
import markdown
import re
import datetime


class simple_markdown:

    markdown_extensions = ["fenced_code"]

    def __init__(self, file_path):
        with open(file_path, "r") as f:
            lines_in = f.readlines()

        self.file_path = file_path
        self.markdown = "".join([x for x in lines_in if not re.match(r"^\@", x)])
        self.html = markdown.markdown(
            self.markdown, extensions=self.markdown_extensions
        )
        self.title = [x for x in lines_in if re.match(r"^\# ", x)][0][1:].strip()
        meta_temp = [x for x in lines_in if re.match(r"^\@", x)]
        meta_temp = [re.split("=", x[1:]) for x in meta_temp]
        meta_temp.append(("title", self.title))
        self.meta = self.consolidate_meta(meta_temp)

    def consolidate_meta(self, meta_seq):
        temp = [
            (self.strip_whitespace(key), self.strip_whitespace(value))
            for key, value in meta_seq
        ]
        keys = set()
        [keys.add(x[0]) for x in temp]

        output = {}
        for this_key in sorted(keys):
            output[this_key] = ",".join([x[1] for x in temp if x[0] == this_key])

        if "finished" in output:
            self.finished = output["finished"] == "True"
        else:
            self.finished = False

        return output

    def strip_whitespace(self, text):
        return re.sub(r"(^\s+)|(\s+$)", "", text)


class site_press:
    def __init__(self, root_dir, css_style=None):
        self.root_dir = root_dir
        self.css_style = css_style

        file_loader = jinja2.FileSystemLoader(os.path.join(root_dir, "templates"))
        self.env = jinja2.Environment(loader=file_loader)

    def make_index(self):
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
        string = string.lower()
        string = string.replace("_", "-")
        string = re.sub(r"\s|\_", "-", string)
        return string

    def blog_path(self, path, dir_out="blog"):
        """Alters a markdown file path to be under the blog directory (on disc)."""
        file_name = self.blog_name(path)
        file_name = os.path.splitext(file_name)[0] + ".html"

        file_out = os.path.join(self.root_dir, dir_out, file_name)
        return file_out

    def blog_name(self, path):
        file_name = self.webify(os.path.split(path)[-1])
        file_name = os.path.splitext(file_name)[0]
        return file_name

    def render_blog(self, file_in):
        file_out = self.blog_path(file_in)
        template = self.env.get_template("page.html")

        blog_in = simple_markdown(file_in)

        page_out = template.render(
            title=blog_in.title,
            style=self.css_style,
            body=blog_in.html,
            metadata=blog_in.meta,
        )

        if blog_in.finished:
            with open(file_out, "w") as f:
                f.writelines(page_out)

        return blog_in

    def render_all_blogs(self):
        page = self.env.get_template("page.html")
        b_list = self.env.get_template("blog_list.html")
        search_dir = os.path.join(self.root_dir, "markdown")
        all_files = os.listdir(search_dir)
        all_files = [x for x in all_files if re.match(r".*\.md$", x)]
        all_files = [os.path.join(search_dir, x) for x in all_files]

        blog_list = []
        for this_blog in all_files:
            temp = self.render_blog(this_blog)
            if temp.finished:
                blog_list.append(temp)

        for this_blog in blog_list:
            this_blog.url = self.blog_name(this_blog.file_path)

        page_out = page.render(
            title="Blogs", style=self.css_style, body=b_list.render(blogs=blog_list)
        )

        with open(self.blog_path("blogs"), "w") as f:
            f.writelines(page_out)


test = site_press(os.path.dirname(os.getcwd()), "/main.css")
test.make_index()
test.render_all_blogs()
