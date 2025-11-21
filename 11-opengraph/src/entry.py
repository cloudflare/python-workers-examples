from workers import WorkerEntrypoint, Request, fetch
from js import HTMLRewriter
from urllib.parse import urlparse
from html import escape

from pyodide.ffi import create_proxy


class MetaTagInjector:
    """
    Element handler for HTMLRewriter that injects OpenGraph meta tags.
    Uses Python's html.escape() for proper HTML escaping.
    """

    def __init__(self, og_data: dict):
        self.og_data = og_data
        self.injected = False

    def element(self, element):
        """Called when the <head> element is encountered."""
        if not self.injected:
            # Create and inject meta tags
            self._inject_meta_tags(element)
            self.injected = True

    def _inject_meta_tags(self, head_element):
        """Inject OpenGraph and Twitter Card meta tags."""
        # OpenGraph tags
        self._create_meta(head_element, "property", "og:title", self.og_data["title"])
        self._create_meta(
            head_element, "property", "og:description", self.og_data["description"]
        )
        self._create_meta(head_element, "property", "og:image", self.og_data["image"])
        self._create_meta(head_element, "property", "og:url", self.og_data["url"])
        self._create_meta(head_element, "property", "og:type", self.og_data["type"])
        self._create_meta(
            head_element, "property", "og:site_name", self.og_data["site_name"]
        )

        # Twitter Card tags
        self._create_meta(head_element, "name", "twitter:card", "summary_large_image")
        self._create_meta(head_element, "name", "twitter:title", self.og_data["title"])
        self._create_meta(
            head_element, "name", "twitter:description", self.og_data["description"]
        )
        self._create_meta(head_element, "name", "twitter:image", self.og_data["image"])

    def _create_meta(self, head_element, attr_name: str, attr_value: str, content: str):
        """
        Create a meta tag and prepend it to the head element.
        Uses Python's html.escape() for proper attribute escaping.
        """
        # Use Python's built-in html.escape() which handles all necessary escaping
        escaped_attr_value = escape(attr_value, quote=True)
        escaped_content = escape(content, quote=True)
        meta_html = (
            f'<meta {attr_name}="{escaped_attr_value}" content="{escaped_content}" />'
        )
        head_element.prepend(meta_html, html=True)


class ExistingMetaRemover:
    """
    Element handler that removes existing OpenGraph and Twitter meta tags.
    """

    def element(self, element):
        """Remove the element by calling remove()."""
        element.remove()


class Default(WorkerEntrypoint):
    """
    OpenGraph Meta Tag Injection Example

    This Worker fetches a web page and injects OpenGraph meta tags
    based on the request path using Cloudflare's HTMLRewriter API.
    """

    async def fetch(self, request: Request):
        # Parse the request path to determine which page we're serving
        url = urlparse(request.url)
        path = url.path

        # Define OpenGraph metadata based on the path
        og_data = self.get_opengraph_data(path)

        # Fetch the original HTML from a target website
        # In this example, we'll use example.com, but you can replace this
        # with your actual website URL
        #
        # Note that this isn't necessary if your worker will also be serving
        # content of your website, in that case you should already have the HTML
        # you're returning ready to go here.
        target_url = f"https://example.com{path}"

        # Fetch the original page
        response = await fetch(target_url)

        # Use HTMLRewriter to inject OpenGraph meta tags
        rewritten_response = self.inject_opengraph_tags(response, og_data)

        return rewritten_response

    def get_opengraph_data(self, path: str) -> dict:
        """
        Generate OpenGraph metadata based on the request path.
        Customize this function to match your site's structure.
        """
        # Default metadata
        og_data = {
            "title": "My Awesome Website",
            "description": "Welcome to my website built with Python Workers!",
            "image": "https://images.unsplash.com/photo-1518770660439-4636190af475",
            "url": f"https://yoursite.com{path}",
            "type": "website",
            "site_name": "Python Workers Demo",
        }

        # Customize based on path
        if path.startswith("/blog/"):
            article_slug = path.replace("/blog/", "").strip("/")
            og_data.update(
                {
                    "title": f"Blog Post: {article_slug.replace('-', ' ').title()}",
                    "description": f"Read our latest article about {article_slug.replace('-', ' ')}",
                    "image": "https://images.unsplash.com/photo-1499750310107-5fef28a66643",
                    "type": "article",
                }
            )
        elif path.startswith("/products/"):
            product_slug = path.replace("/products/", "").strip("/")
            og_data.update(
                {
                    "title": f"Product: {product_slug.replace('-', ' ').title()}",
                    "description": f"Check out our amazing {product_slug.replace('-', ' ')} product",
                    "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
                    "type": "product",
                }
            )
        elif path == "/about":
            og_data.update(
                {
                    "title": "About Us - Python Workers",
                    "description": "Learn more about our team and what we do with Python Workers",
                    "image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c",
                }
            )

        return og_data

    def inject_opengraph_tags(self, response, og_data: dict):
        """
        Use HTMLRewriter to inject OpenGraph meta tags into the HTML response.
        Removes existing OG tags first to avoid duplicates.
        """
        # Create an HTMLRewriter instance
        rewriter = HTMLRewriter.new()

        meta_remover = create_proxy(ExistingMetaRemover())
        meta_injector = create_proxy(MetaTagInjector(og_data))

        rewriter = HTMLRewriter.new()
        # Remove existing OpenGraph and Twitter meta tags to avoid duplicates
        rewriter.on('meta[property^="og:"]', meta_remover)
        rewriter.on('meta[name^="twitter:"]', meta_remover)
        # Inject new OpenGraph meta tags into the <head> element
        rewriter.on("head", meta_injector)

        return rewriter.transform(response.js_object)
