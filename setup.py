"""Legacy setuptools entrypoint (pyproject.toml is the source of truth).

Kept for compatibility with tooling that still expects `python setup.py`.
"""

from setuptools import find_packages, setup

setup(
    name="databricks-connector",
    version="1.0.2",
    description="Enterprise FastAPI connector for the Databricks REST API.",
    packages=find_packages(include=["databricks_connector", "databricks_connector.*"]),
    python_requires=">=3.12",
    install_requires=[
        "fastapi==0.115.6",
        "uvicorn[standard]==0.34.0",
        "pydantic==2.10.4",
        "pydantic-settings==2.7.1",
        "httpx==0.28.1",
        "tenacity==9.0.0",
        "prometheus-client==0.21.1",
    ],
    entry_points={
        "console_scripts": ["databricks-connector=databricks_connector.main:run"],
    },
)
