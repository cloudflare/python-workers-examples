# Image Generation with Pillow Example

This example demonstrates how to build a Python Worker that dynamically generates images using the Pillow (PIL) library.

## What It Does

The Worker provides four different image generation endpoints:
1. **Gradient Generator** (`/gradient`) - Creates gradient images with customizable colors and dimensions
2. **Badge Generator** (`/badge`) - Generates badges or buttons with text
3. **Placeholder Generator** (`/placeholder`) - Creates placeholder images with dimensions displayed
4. **Chart Generator** (`/chart`) - Produces simple bar charts

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run `uv run pywrangler dev` within this directory, it should use the config
in `wrangler.jsonc` to run the example.

```bash
uv run pywrangler dev
```

Then visit:
- `http://localhost:8787/` - Interactive demo page with all examples
- `http://localhost:8787/gradient?width=600&height=300&color1=FF6B6B&color2=4ECDC4` - Gradient image
- `http://localhost:8787/badge?text=Python+Workers&bg_color=2196F3` - Custom badge
- `http://localhost:8787/placeholder?width=500&height=300` - Placeholder image
- `http://localhost:8787/chart?values=15,30,25,40,20&labels=Mon,Tue,Wed,Thu,Fri` - Bar chart

## Deployment

Deploy to Cloudflare Workers:

```bash
uv run pywrangler deploy
```

## Learn More

- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Python Workers Documentation](https://developers.cloudflare.com/workers/languages/python/)
- [ImageDraw Reference](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
