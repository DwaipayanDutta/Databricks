"""Service layer for the Workspace API (notebooks/folders): /api/2.0/workspace"""

from __future__ import annotations

from typing import Any

from databricks_connector.core.client import DatabricksClient

_BASE = "/api/2.0/workspace"


class NotebookService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def import_notebook(
        self, path: str, content: str, language: str, fmt: str, overwrite: bool
    ) -> dict[str, Any]:
        body = {
            "path": path,
            "content": content,
            "language": language,
            "format": fmt,
            "overwrite": overwrite,
        }
        return await self._client.post(f"{_BASE}/import", json_body=body)

    async def export_notebook(self, path: str, fmt: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/export", params={"path": path, "format": fmt})

    async def list_workspace(self, path: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/list", params={"path": path})

    async def delete_object(self, path: str, recursive: bool) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/delete", json_body={"path": path, "recursive": recursive})

    async def get_status(self, path: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/get-status", params={"path": path})

    async def create_folder(self, path: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/mkdirs", json_body={"path": path})

    async def _export_content_and_language(self, path: str) -> tuple[str, str]:
        """Shared by move/copy: export a notebook's source and detect its
        language, since the public Workspace API has no dedicated
        "move"/"copy" verb -- both are emulated via export + import.
        """
        exported = await self.export_notebook(path, "SOURCE")
        content = exported.get("content", "")
        language = exported.get("language", "PYTHON")
        return content, language

    async def move_object(self, source_path: str, destination_path: str) -> dict[str, Any]:
        content, language = await self._export_content_and_language(source_path)
        await self.import_notebook(destination_path, content, language, "SOURCE", True)
        await self.delete_object(source_path, recursive=False)
        return {"source_path": source_path, "destination_path": destination_path, "moved": True}

    async def copy_object(self, source_path: str, destination_path: str, overwrite: bool) -> dict[str, Any]:
        content, language = await self._export_content_and_language(source_path)
        result = await self.import_notebook(destination_path, content, language, "SOURCE", overwrite)
        return {"source_path": source_path, "destination_path": destination_path, "copied": True, **result}
