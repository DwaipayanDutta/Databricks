"""Legacy setuptools entrypoint (pyproject.toml is the source of truth).

Kept for compatibility with tooling that still expects `python setup.py`.
"""

from setuptools import find_packages, setup

setup(
    name="databricks-connector",
    version="1.1.0",
    description="Enterprise FastAPI connector for the Databricks REST API.",
    packages=find_packages(include=["databricks_connector", "databricks_connector.*"]),
    python_requires=">=3.12",
    # Kept in lockstep with pyproject.toml's [project.dependencies] -- this
    # previously pinned fastapi==0.115.6, whose own dependency ceiling
    # (starlette<0.42.0) made it impossible to get a patched starlette (see
    # CHANGELOG.md [1.0.3] "Security"). `python setup.py install` would have
    # silently reintroduced that CVE-affected pin even after pyproject.toml
    # was fixed. Extras are intentionally omitted here to match `pip install .`
    # (base install); use `pip install -e .[cache,otel,dev]` for extras.
    install_requires=[
        "fastapi==0.141.1",
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
