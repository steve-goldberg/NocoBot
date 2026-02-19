from setuptools import setup


# When building from nocodb/ folder, packages are in current directory
# We need to map them to nocodb.* namespace for imports like "from nocodb.mcpserver import ..."
setup(
   name='nocodb',
   version='3.0.0',
   author='Steve Goldberg',
   author_email='',
   packages=['nocodb', 'nocodb.mcpserver', 'nocodb.mcpserver.tools', 'nocodb.cli', 'nocodb.filters', 'nocodb.infra'],
   package_dir={
       'nocodb': '.',
       'nocodb.mcpserver': 'mcpserver',
       'nocodb.mcpserver.tools': 'mcpserver/tools',
       'nocodb.cli': 'cli',
       'nocodb.filters': 'filters',
       'nocodb.infra': 'infra',
   },
   license='AGPL-3.0',
   url='https://github.com/steve-goldberg/nocodb-py',
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
       "cli": [
           # CLI is now auto-generated from MCP server
           # Uses cyclopts (via fastmcp) instead of typer
           "fastmcp>=3.0.0",
           "tomli>=2.0.0;python_version<'3.11'",
       ],
       "mcp": [
           "fastmcp>=3.0.0",
       ],
       "all": [
           "fastmcp>=3.0.0",
           "tomli>=2.0.0;python_version<'3.11'",
       ],
   },
   entry_points={
       "console_scripts": [
           "nocodb=nocodb.cli.main:main",
       ],
   },
   python_requires=">=3.10",
)
