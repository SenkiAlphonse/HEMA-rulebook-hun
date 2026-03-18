"""
Setup configuration for HEMA Rulebook Q&A Tools package
"""

from setuptools import setup, find_packages

setup(
    name="qa-tools",
    version="1.0.0",
    description="Q&A tools and search engine for HEMA rulebook",
    author="HEMA Rulebook Project",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    install_requires=[
        "mistune>=2.0.0",
        "flask>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "hema-search=qa_tools.search_engine.search_aliases:main",
            "hema-demo=qa_tools.tools.demo_search:main",
        ],
    },
)
