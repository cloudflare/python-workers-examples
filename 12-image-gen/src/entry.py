from workers import WorkerEntrypoint, Response, Request
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from urllib.parse import urlparse, parse_qs
import random
from pathlib import Path

from pyodide.ffi import to_js


class Default(WorkerEntrypoint):
    """
    Image Generation Example using Pillow (PIL)

    This Worker demonstrates how to use the Pillow library to dynamically
    generate images in a Cloudflare Python Worker. It showcases various
    image generation techniques including gradients, text rendering, shapes,
    and more.

    Available endpoints:
    - /gradient - Generate a colorful gradient image
    - /badge - Generate a badge with custom text
    - /placeholder - Generate a placeholder image with dimensions
    - /chart - Generate a simple bar chart
    - / - Show available endpoints
    """

    async def fetch(self, request: Request):
        # Parse the request URL to determine which image to generate
        url = urlparse(request.url)
        path = url.path

        # Parse query parameters for customization
        query_params = parse_qs(url.query)

        # Route to different image generators based on path
        if path == "/gradient":
            return self.generate_gradient(query_params)
        elif path == "/badge":
            return self.generate_badge(query_params)
        elif path == "/placeholder":
            return self.generate_placeholder(query_params)
        elif path == "/chart":
            return self.generate_chart(query_params)
        else:
            # Return a simple HTML page showing available endpoints
            return self.show_endpoints()

    def generate_gradient(self, params: dict) -> Response:
        """
        Generate a gradient image.

        Query parameters:
        - width: Image width (default: 800)
        - height: Image height (default: 400)
        - color1: Start color in hex (default: random)
        - color2: End color in hex (default: random)
        """
        # Get dimensions from query params or use defaults
        width = int(params.get("width", [800])[0])
        height = int(params.get("height", [400])[0])

        # Get colors or generate random ones
        color1 = params.get("color1", [None])[0]
        color2 = params.get("color2", [None])[0]

        if not color1:
            color1 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        if not color2:
            color2 = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        # Convert hex colors to RGB tuples
        r1, g1, b1 = self.hex_to_rgb(color1)
        r2, g2, b2 = self.hex_to_rgb(color2)

        # Create a new image with RGB mode
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)

        # Draw gradient by interpolating between colors
        for y in range(height):
            # Calculate interpolation factor (0.0 to 1.0)
            factor = y / height

            # Interpolate each color channel
            r = int(r1 + (r2 - r1) * factor)
            g = int(g1 + (g2 - g1) * factor)
            b = int(b1 + (b2 - b1) * factor)

            # Draw a horizontal line with the interpolated color
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Convert image to bytes and return as PNG
        return self.image_to_response(image, "image/png")

    def generate_badge(self, params: dict) -> Response:
        """
        Generate a badge/button with custom text.

        Query parameters:
        - text: Badge text (default: "Hello World")
        - bg_color: Background color in hex (default: #4CAF50)
        - text_color: Text color in hex (default: #FFFFFF)
        """
        # Get parameters
        text = params.get("text", ["Hello World"])[0]
        bg_color = params.get("bg_color", ["#4CAF50"])[0]
        text_color = params.get("text_color", ["#FFFFFF"])[0]

        # Convert hex colors to RGB
        bg_rgb = self.hex_to_rgb(bg_color)
        text_rgb = self.hex_to_rgb(text_color)

        # Create image with padding for text
        # We'll estimate size based on text length
        padding = 20

        # Create a temporary image to measure text size
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)

        # Use default font (Pillow's built-in font)
        # Note: In a production environment, you might want to include custom fonts
        font = ImageFont.load_default()

        # Get text bounding box to calculate required image size
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Create the actual image with proper dimensions
        width = text_width + (padding * 2)
        height = text_height + (padding * 2)

        image = Image.new("RGB", (width, height), bg_rgb)
        draw = ImageDraw.Draw(image)

        # Draw rounded rectangle background (simulate with rectangle for simplicity)
        # Draw the text centered
        text_x = padding
        text_y = padding
        draw.text((text_x, text_y), text, fill=text_rgb, font=font)

        return self.image_to_response(image, "image/png")

    def generate_placeholder(self, params: dict) -> Response:
        """
        Generate a placeholder image with dimensions displayed.

        Query parameters:
        - width: Image width (default: 400)
        - height: Image height (default: 300)
        - bg_color: Background color in hex (default: #CCCCCC)
        - text_color: Text color in hex (default: #666666)
        """
        # Get dimensions
        width = int(params.get("width", [400])[0])
        height = int(params.get("height", [300])[0])
        bg_color = params.get("bg_color", ["#CCCCCC"])[0]
        text_color = params.get("text_color", ["#666666"])[0]

        # Convert colors
        bg_rgb = self.hex_to_rgb(bg_color)
        text_rgb = self.hex_to_rgb(text_color)

        # Create image
        image = Image.new("RGB", (width, height), bg_rgb)
        draw = ImageDraw.Draw(image)

        # Draw an X across the image
        draw.line([(0, 0), (width, height)], fill=text_rgb, width=2)
        draw.line([(width, 0), (0, height)], fill=text_rgb, width=2)

        # Draw border
        draw.rectangle([(0, 0), (width - 1, height - 1)], outline=text_rgb, width=2)

        # Add dimensions text in the center
        text = f"{width} × {height}"

        font = ImageFont.load_default()

        # Get text size and center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2

        # Draw text with a background for better visibility
        padding = 10
        draw.rectangle(
            [
                (text_x - padding, text_y - padding),
                (text_x + text_width + padding, text_y + text_height + padding),
            ],
            fill=bg_rgb,
        )
        draw.text((text_x, text_y), text, fill=text_rgb, font=font)

        return self.image_to_response(image, "image/png")

    def generate_chart(self, params: dict) -> Response:
        """
        Generate a simple bar chart.

        Query parameters:
        - values: Comma-separated values (default: 10,25,15,30,20)
        - labels: Comma-separated labels (default: A,B,C,D,E)
        - color: Bar color in hex (default: #2196F3)
        """
        # Parse values and labels
        values_str = params.get("values", ["10,25,15,30,20"])[0]
        values = [int(v.strip()) for v in values_str.split(",")]

        labels_str = params.get("labels", ["A,B,C,D,E"])[0]
        labels = [label.strip() for label in labels_str.split(",")]

        bar_color = params.get("color", ["#2196F3"])[0]
        bar_rgb = self.hex_to_rgb(bar_color)

        # Chart dimensions
        width = 600
        height = 400
        padding = 50
        chart_width = width - (padding * 2)
        chart_height = height - (padding * 2)

        # Create image with white background
        image = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Draw axes
        draw.line(
            [(padding, padding), (padding, height - padding)], fill=(0, 0, 0), width=2
        )  # Y-axis
        draw.line(
            [(padding, height - padding), (width - padding, height - padding)],
            fill=(0, 0, 0),
            width=2,
        )  # X-axis

        # Calculate bar dimensions
        num_bars = len(values)
        bar_width = chart_width // (num_bars * 2)
        spacing = bar_width
        max_value = max(values) if values else 1

        # Draw bars
        font = ImageFont.load_default()

        for i, (value, label) in enumerate(zip(values, labels)):
            # Calculate bar position and height
            bar_height = int((value / max_value) * chart_height)
            x = padding + spacing + (i * (bar_width + spacing))
            y = height - padding - bar_height

            # Draw bar
            draw.rectangle(
                [(x, y), (x + bar_width, height - padding)],
                fill=bar_rgb,
                outline=(0, 0, 0),
            )

            # Draw value on top of bar
            value_text = str(value)
            bbox = draw.textbbox((0, 0), value_text, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (x + (bar_width - text_width) // 2, y - 20),
                value_text,
                fill=(0, 0, 0),
                font=font,
            )

            # Draw label below bar
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (x + (bar_width - text_width) // 2, height - padding + 5),
                label,
                fill=(0, 0, 0),
                font=font,
            )

        return self.image_to_response(image, "image/png")

    def hex_to_rgb(self, hex_color: str) -> tuple:
        """
        Convert a hex color string to an RGB tuple.

        Args:
            hex_color: Color in format "#RRGGBB" or "RRGGBB"

        Returns:
            Tuple of (R, G, B) values
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip("#")

        # Convert to RGB
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def image_to_response(self, image: Image.Image, content_type: str) -> Response:
        """
        Convert a PIL Image to a Response object.

        Args:
            image: PIL Image object
            content_type: MIME type for the response

        Returns:
            Response object with image data
        """
        # Create a BytesIO buffer to hold the image data
        buffer = BytesIO()

        # Save image to buffer in PNG format
        image.save(buffer, format="PNG")

        image_bytes = buffer.getvalue()

        # Create and return response with appropriate headers
        #
        # TODO: This currently performs an unnecessary copy, need to fix.
        return Response(
            to_js(image_bytes).buffer,
            headers={
                "Content-Type": content_type,
                "Cache-Control": "public, max-age=3600",
            },
        )

    def show_endpoints(self) -> Response:
        """
        Return an HTML page showing available endpoints and examples.
        """
        index = Path(__file__).parent / "index.html"
        return Response(index.read_text(), headers={"Content-Type": "text/html"})
