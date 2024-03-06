"""
Tools to build my website from Markdown.
"""
import dataclasses
import datetime
import glob
import os
import re
from typing import Any
from urllib import parse

import bs4
import jinja2
import markdown
import yaml
from markdown.extensions.wikilinks import WikiLinkExtension


class SiteBuilder:
    """
    Main process that controls the construction of the website.
    """

    def __init__(
        self, input_dir: str, output_dir: str, template_dir: str, base_url: str = "/"
    ) -> None:
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.base_url = base_url

        file_loader = jinja2.FileSystemLoader(template_dir)
        self.env = jinja2.Environment(loader=file_loader)
        self.env.globals["url"] = self.url

    def run(self) -> None:
        """Run the whole process."""
        files = glob.glob(os.path.join(self.input_dir, "**", "*.md"), recursive=True)

        # Initial rendering
        posts: list["Post"] = []
        valid_links: set[str] = set()
        for the_file in files:
            with open(the_file, encoding="utf-8") as file:
                the_post = render_markdown(file.read())
            the_post.src_path = the_file
            the_post.url = path_to_url(os.path.relpath(the_file, self.input_dir))
            the_post.dst_path = os.path.abspath(
                os.path.join(self.output_dir, the_post.url)
            )
            if the_post.metadata.get("published") is None:
                continue
            posts.append(the_post)
            valid_links.add(the_post.metadata.get("title"))

        # Post-processing
        for the_post in posts:
            for the_link in the_post.soup.find_all("a"):
                the_url = the_link.get("href")
                if not isinstance(the_url, str):
                    continue
                elif the_url in valid_links:
                    continue
                elif the_url.startswith("http"):
                    continue
                else:
                    the_link.replace_with(the_link.text)
            for the_image in the_post.soup.find_all("img"):
                the_url = the_image.get("src")
                if not isinstance(the_url, str):
                    continue
                the_image["src"] = self.url(the_url)

        # Output the final HTML
        template = self.env.get_template("blog.html")
        for the_post in posts:
            print(the_post.dst_path)
            with open(the_post.dst_path, "w", encoding="utf-8") as file:
                file.write(
                    template.render(
                        metadata=the_post.metadata,
                        post=the_post,
                    )
                )

        # Generate a main set of links
        posts_by_month = {}
        for the_post in sorted(posts, key=lambda x: x.publish_date, reverse=True):
            the_month = the_post.publish_date.strftime("%B %Y")
            if the_month not in posts_by_month:
                posts_by_month[the_month] = []
            posts_by_month[the_month].append(the_post)

        template = self.env.get_template("blog_list.html")
        with open(
            os.path.join(self.output_dir, "blogs.html"), "w", encoding="utf-8"
        ) as file:
            file.write(
                template.render(
                    metadata={"title": "Blogs"},
                    posts_by_month=posts_by_month,
                )
            )

        with open(
            os.path.join(self.output_dir, "index.html"), "w", encoding="utf-8"
        ) as file:
            file.write(
                self.env.get_template("index.html").render(
                    metadata={"title": "Joe McGrath - Home page"}
                )
            )

        # TODO : Tag pages
        # TODO : RSS feed

    def url(self, path: str) -> str:
        if re.search(r"(?i)^[A-Z]\:[\\|/].*", self.base_url):
            # File paths - do local rendering.
            return "file:///" + os.path.join(self.base_url, path).replace("\\", "/")

        return parse.urljoin(self.base_url, path)


@dataclasses.dataclass
class Post:
    """
    An individual blog post.
    """

    markdown: str
    soup: bs4.BeautifulSoup
    metadata: dict[str, Any]

    src_path: str = ""
    dst_path: str = ""
    url: str = ""

    @property
    def tags(self) -> list[str]:
        """The tags describing this post."""
        return self.metadata.get("tags", [])

    @property
    def html(self) -> str:
        """The rendered HTML for this post."""
        return self.soup.prettify()

    @property
    def publish_date(self) -> datetime.datetime:
        """Get a publish date for the post."""
        return self.metadata.get("published", datetime.datetime.now())


def render_markdown(markdown_text: str) -> Post:
    """
    Convert notebook-style Markdown into ready-to-use HTML.
    """

    # Set up markdown -> HTML renderer.
    markdown_parser = markdown.Markdown(
        extensions=[
            "fenced_code",
            "meta",
            "tables",
            # Using the default syntax highlighting.
            "codehilite",
            WikiLinkExtension(),
            WikiLinkExtension(base_url="", end_url=""),
            # WikiLinkExtension(base_url='./blog/',end_url='.html'),
        ]
    )

    # Extract any frontmatter
    lines = markdown_text.split("\n")
    standard_meta = {
        "title": "",
        "tags": [],
        "published": None,
    }
    meta_block = []
    has_meta = False
    line_no = 0
    for line_no, line in enumerate(lines):
        if line.startswith("---"):
            if line_no == 0:
                has_meta = True
            else:
                break
        else:
            meta_block.append(line)
    if has_meta:
        meta = yaml.safe_load("\n".join(meta_block))
        meta = {**standard_meta.copy(), **meta}
        body = "\n".join(lines[line_no + 1 :]).strip()
    else:
        body = "\n".join(lines).strip()
        meta = standard_meta.copy()

    # Tidy up metadata
    allowed_meta = {"tags", "title", "published"}
    meta = {x: y for x, y in meta.items() if x in allowed_meta}

    # Post-process the HTML
    soup = bs4.BeautifulSoup(markdown_parser.convert(body), features="html.parser")

    # Drop heading tags down one level (I write with multiple H1 elements).
    replacements = ["h6", "h5", "h4", "h3", "h2", "h1"]
    for n, the_target in enumerate(replacements[1:]):
        for the_tag in soup.find_all(the_target):
            new_tag = soup.new_tag(replacements[n])
            new_tag.string = the_tag.text

            the_tag.replace_with(new_tag)

    return Post(
        markdown=markdown_text,
        soup=soup,
        metadata=meta,
    )


def path_to_url(path: str) -> str:
    """Convert a file path to a URL."""
    url = re.sub(r"[\s\_-]+", "-", path.lower())
    url = f"./{os.path.splitext(url)[0]}.html"
    url = url.replace("\\", "/")

    return url


if __name__ == "__main__":
    builder = SiteBuilder(
        r"./markdown",
        r".",
        r"./templates",
    )
    builder.run()
