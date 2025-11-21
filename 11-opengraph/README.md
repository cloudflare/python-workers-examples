# OpenGraph Meta Tag Injection Example

This example demonstrates how to build a Python Worker that dynamically injects OpenGraph meta tags into web pages based on the request path. This is perfect for controlling how your content appears when shared on social media platforms like Facebook, Twitter, LinkedIn, and Slack.

## What It Does

The Worker:
1. **Receives a request** for a specific URL path (e.g., `/blog/my-article`)
2. **Generates OpenGraph metadata** dynamically based on the path
3. **Fetches the original HTML** from your target website
4. **Uses Cloudflare's HTMLRewriter** to inject OpenGraph meta tags into the HTML `<head>` section
5. **Returns the enhanced HTML** with proper social media preview tags

This example showcases how to use Cloudflare's powerful HTMLRewriter API from Python Workers via the `js` module interop.

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run `uv run pywrangler dev` within this directory, it should use the config
in `wrangler.jsonc` to run the example.

```bash
uv run pywrangler dev
```

Then visit:
- `http://localhost:8787/` - Home page with default metadata
- `http://localhost:8787/blog/python-workers-intro` - Blog post example
- `http://localhost:8787/products/awesome-widget` - Product page example
- `http://localhost:8787/about` - About page example

## Deployment

Deploy to Cloudflare Workers:

```bash
uv run pywrangler deploy
```

## Customization

To adapt this example for your own website:

1. **Update the target URL** in `src/entry.py`:
   ```python
   target_url = f"https://your-website.com{path}"
   ```

2. **Customize metadata patterns** in the `get_opengraph_data()` method:
   ```python
   if path.startswith("/your-section/"):
       og_data.update({
           "title": "Your Custom Title",
           "description": "Your custom description",
           "image": "https://your-image-url.com/image.jpg"
       })
   ```

3. **Add more URL patterns** to match your site structure

## Testing Your OpenGraph Tags

Use these tools to validate your OpenGraph tags:
- [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
- [X Card Validator](https://cards-dev.x.com/validator)
- [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/)
