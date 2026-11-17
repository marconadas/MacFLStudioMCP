from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-flstudio",
    version="0.1.0",
    description="Agent-native CLI for FL Studio: every fl-studio-mcp tool as a shell command",
    license="MIT",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={"cli_anything.flstudio": ["README.md", "skills/*.md", "tests/TEST.md"]},
    # fl-studio-mcp (this repo) is deliberately NOT listed: an unrelated package with that name is on
    # PyPI. Install both from the checkout: uv tool install -e agent-harness --with-editable .
    install_requires=["click>=8"],
    entry_points={"console_scripts": ["cli-anything-flstudio=cli_anything.flstudio.flstudio_cli:main"]},
)
