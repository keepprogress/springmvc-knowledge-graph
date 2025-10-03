"""Setup script for SpringMVC Knowledge Graph Analyzer"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme = Path(__file__).parent / "README.md"
long_description = readme.read_text(encoding="utf-8") if readme.exists() else ""

setup(
    name="springmvc-knowledge-graph",
    version="0.1.0",
    description="Automatic knowledge graph builder for SpringMVC projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="keepprogress",
    author_email="keepprogress@gmail.com",
    url="https://github.com/keepprogress/springmvc-knowledge-graph",

    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs"]),

    python_requires=">=3.10",

    install_requires=[
        "claude-agent-sdk>=0.1.0",
        "mcp>=1.0.0",
        "pyyaml>=6.0",
        "click>=8.0",
        "javalang>=0.13.0",
        "lxml>=4.9.0",
        "networkx>=3.0",
        "rich>=13.0",
        "oracledb>=2.0.0",  # Oracle 資料庫連線（Python-only，不需 Oracle Client）
    ],

    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },

    # CLI entry points will be added in Phase 6.4
    # entry_points={
    #     "console_scripts": [
    #         "springmvc-analyzer=cli.springmvc_cli:main",
    #     ],
    # },

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Documentation",
    ],

    keywords="springmvc mybatis knowledge-graph code-analysis claude-agent mcp oracle",

    project_urls={
        "Documentation": "https://github.com/keepprogress/springmvc-knowledge-graph",
        "Source": "https://github.com/keepprogress/springmvc-knowledge-graph",
        "Tracker": "https://github.com/keepprogress/springmvc-knowledge-graph/issues",
    },
)
