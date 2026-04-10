"""Image generation server that runs inside a Cloudflare Container.

Generates random abstract art using Pillow and serves it over HTTP.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import parse_qs, urlparse
import random

from PIL import Image, ImageDraw, ImageFilter


def generate_image(width=512, height=512, seed=None):
    """Generate a random abstract art image."""
    if seed is not None:
        random.seed(seed)

    img = Image.new("RGB", (width, height), _random_color(pastel=True))
    draw = ImageDraw.Draw(img)

    # Layer random shapes
    for _ in range(random.randint(15, 40)):
        shape = random.choice(["circle", "rect", "line"])
        color = _random_color()

        if shape == "circle":
            cx = random.randint(0, width)
            cy = random.randint(0, height)
            r = random.randint(10, min(width, height) // 3)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        elif shape == "rect":
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = x1 + random.randint(20, width // 2)
            y2 = y1 + random.randint(20, height // 2)
            draw.rectangle([x1, y1, x2, y2], fill=color)
        else:
            points = [
                (random.randint(0, width), random.randint(0, height))
                for _ in range(random.randint(2, 5))
            ]
            draw.line(points, fill=color, width=random.randint(1, 8))

    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 2.0)))
    return img


def _random_color(pastel=False):
    if pastel:
        return tuple(random.randint(180, 255) for _ in range(3))
    return tuple(random.randint(0, 255) for _ in range(3))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        width = min(int(params.get("w", [512])[0]), 2048)
        height = min(int(params.get("h", [512])[0]), 2048)
        seed = params.get("seed", [None])[0]
        if seed is not None:
            seed = int(seed)

        img = generate_image(width, height, seed)

        buf = BytesIO()
        img.save(buf, format="PNG")
        body = buf.getvalue()

        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[container] {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), Handler)
    print("[container] listening on port 8080")
    server.serve_forever()
