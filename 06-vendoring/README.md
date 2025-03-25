# Vendoring Packages: FastAPI + Jinja2 Example

*Note: You must have Python Packages enabled on your account for built-in packages to work. Request Access to our Closed Beta using [This Form](https://forms.gle/FcjjhV3YtPyjRPaL8)*

This is an example of a Python Worker that uses a built-in package (FastAPI) with a vendored package (Jinja2).

## Adding Packages

Built-in packages can be selected from [this list](https://developers.cloudflare.com/workers/languages/python/packages/#supported-packages) and added to your `requirements.txt` file. These can be used with no other explicit install step.

Vendored packages are added to your source files and need to be installed in a special manner. The Python Workers team plans to make this process automatic in the future, but for now, manual steps need to be taken.

### Vendoring Packages

First, install Python3.12 and pip for Python 3.12.

*Currently, other versions of Python will not work - use 3.12!*

The easiest way to install Python 3.12 is using uv, so install it by following
https://docs.astral.sh/uv/getting-started/installation/.

Then run:

```console
uv python install 3.12
```

Then create a virtual environment and activate it from your shell:

```console
uv venv -p 3.12
# activate the venv using the command `uv` has given you
# usually `source .venv/bin/activate` or `.venv\Scripts\activate`
```

Within our virtual environment, install the pyodide CLI:

```console
uv pip install pyodide-build
.\.venv\Scripts\pyodide.exe venv .venv-pyodide
```

Next, add packages to your vendor.txt file. Here we'll add jinja2
```
jinja2
```

Lastly, add these packages to your source files at `src/vendor`. For any additional packages, re-run this command.
```console
.venv-pyodide/bin/pip install -t src/vendor -r vendor.txt
```

### Using Vendored packages

In your wrangler.toml, make the vendor directory available:

```toml
[[rules]]
globs = ["vendor/**"]
type = "Data"
fallthrough = true
```

Now, you can import and use the packages:

```python
import jinja2
# ... etc ...
```

### Developing and Deploying

To develop your Worker, run `wrangler dev`.

To deploy your Worker, run `wrangler deploy`.
