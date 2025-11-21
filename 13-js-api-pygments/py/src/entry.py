from workers import WorkerEntrypoint, Response, Request
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request):
        return Response("Python RPC server is running. Use RPC to call methods.")

    async def highlight_code(self, code: str, language: str = None) -> dict:
        """
        Syntax highlight code using Pygments.

        Args:
            code: The source code to highlight
            language: Programming language (e.g., 'python', 'javascript', 'rust')
                     If None, will attempt to guess the language

        Returns:
            Dict with highlighted HTML and CSS
        """
        try:
            # Get the appropriate lexer
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                lexer = guess_lexer(code)
        except ClassNotFound:
            return {
                "error": f"Language '{language}' not found",
                "html": f"<pre>{code}</pre>",
                "css": "",
                "language": "unknown",
            }

        # Create formatter with line numbers and styling
        formatter = HtmlFormatter(linenos=True, cssclass="highlight", style="monokai")

        # Generate highlighted HTML
        highlighted_html = highlight(code, lexer, formatter)

        # Get the CSS for styling
        css = formatter.get_style_defs(".highlight")

        return {
            "html": highlighted_html,
            "css": css,
            "language": lexer.name,
            "language_alias": lexer.aliases[0] if lexer.aliases else None,
        }
