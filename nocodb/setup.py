import re
from pathlib import Path

from setuptools import setup


def get_version():
    init = Path(__file__).parent / "__init__.py"
    return re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text()).group(1)


# When building from nocodb/ folder, packages are in current directory
# We need to map them to nocodb.* namespace for imports like "from nocodb.mcpserver import ..."
setup(
   name='nocodb',
   version=get_version(),
   author='Steve Goldberg',
   author_email='',
   packages=['nocodb', 'nocodb.mcpserver', 'nocodb.mcpserver.tools', 'nocodb.mcpserver.resources', 'nocodb.cli', 'nocodb.filters', 'nocodb.infra'],
   package_dir={
       'nocodb': '.',
       'nocodb.mcpserver': 'mcpserver',
       'nocodb.mcpserver.tools': 'mcpserver/tools',
       'nocodb.mcpserver.resources': 'mcpserver/resources',
       'nocodb.cli': 'cli',
       'nocodb.filters': 'filters',
       'nocodb.infra': 'infra',
   },
   package_data={'nocodb': ['mcpserver/resources/*.md']},
   license='AGPL-3.0',
   url='https://github.com/steve-goldberg/NocoBot',
   classifiers=[
       "Programming Language :: Python :: 3",
       "License :: OSI Approved :: GNU Affero General Public License v3",
       "Operating System :: OS Independent",
   ],
   description='A Python client for NocoDB v3 API',
   long_description=open('README.md').read(),
   long_description_content_type="text/markdown",
   install_requires=[
       "requests>=2.0",
   ],
   extras_require={
       # FastMCP is pinned >=4.0.5,<5 at every site.
       #
       # Floor == the tested version, following the convention set when the 3.x
       # floor was raised to the version the cap resolved to. FastMCP 4 is built
       # on MCP Python SDK v2, which renames every protocol model field
       # camelCase -> snake_case, so 4.x is not substitutable for 3.x here.
       #
       # The <5 cap is deliberate. FastMCP 5 already has removals scheduled (the
       # bare-string Client("server.py") form warns in 4.x and goes away in 5),
       # and this package is deployed with auto-deploy-on-push. An uncapped
       # specifier is what allowed an unrelated edit to ship a major version
       # bump to production; that exposure is not worth reopening for the sake
       # of an upgrade nobody has tested. Raise the cap deliberately, as here.
       "cli": [
           # CLI is now auto-generated from MCP server
           # Uses cyclopts (via fastmcp) instead of typer
           "fastmcp>=4.0.5,<5",
           "tomli>=2.0.0;python_version<'3.11'",
       ],
       "mcp": [
           "fastmcp>=4.0.5,<5",
       ],
       "all": [
           "fastmcp>=4.0.5,<5",
           "tomli>=2.0.0;python_version<'3.11'",
       ],
       # Test-only dependencies. Deliberately not folded into "all": the
       # Dockerfile installs ".[mcp]", and these should never reach an image.
       # python-dotenv is imported by tests/test_integration_full.py and was
       # previously undeclared, resolving only because another package
       # happened to pull it in.
       "test": [
           "pytest>=7.0.0",
           "pytest-asyncio>=0.21.0",
           "python-dotenv>=1.0.0",
           # The MCP server tests import fastmcp and drive its ASGI app.
           "fastmcp>=4.0.5,<5",
           # The auth tests (T4-T6) drive mcp.http_app() through httpx's
           # ASGITransport, because the in-memory client bypasses HTTP
           # middleware and so never exercises authentication. Declared
           # explicitly: FastMCP 4 moved to httpx2, so plain httpx no longer
           # arrives transitively with fastmcp.
           "httpx>=0.25.0",
       ],
   },
   entry_points={
       "console_scripts": [
           "nocodb=nocodb.cli.main:main",
       ],
   },
   python_requires=">=3.10",
)
