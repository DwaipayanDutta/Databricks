"""Service layer for DBFS: /api/2.0/dbfs

Note: Databricks has deprecated the DBFS root and DBFS mounts (as of early
2026) in favor of Unity Catalog volumes, external locations, and workspace
files; new workspaces may be provisioned without DBFS root access at all.
The REST endpoints wrapped here remain live and documented, so this
service is kept functional and unchanged, but new integrations should
prefer `UnityCatalogService`'s volume operations where possible.
"""

from __future__ import annotations

from typing import Any

from databricks_connector.core.client import DatabricksClient

_BASE = "/api/2.0/dbfs"


class DbfsService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def list_dir(self, path: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/list", params={"path": path})

    async def get_status(self, path: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/get-status", params={"path": path})

    async def mkdirs(self, path: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/mkdirs", json_body={"path": path})

    async def move(self, source_path: str, destination_path: str) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/move", json_body={"source_path": source_path, "destination_path": destination_path}
        )

    async def delete(self, path: str, recursive: bool) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/delete", json_body={"path": path, "recursive": recursive})

    async def read(self, path: str, offset: int, length: int) -> dict[str, Any]:
        return await self._client.get(
            f"{_BASE}/read", params={"path": path, "offset": offset, "length": length}
        )

    async def put(self, path: str, contents: str, overwrite: bool) -> dict[str, Any]:
        """Small-file convenience upload (single request, base64 contents)."""
        return await self._client.post(
            f"{_BASE}/put", json_body={"path": path, "contents": contents, "overwrite": overwrite}
        )

    async def create(self, path: str, overwrite: bool) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/create", json_body={"path": path, "overwrite": overwrite})

    async def add_block(self, handle: int, data: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/add-block", json_body={"handle": handle, "data": data})

    async def close(self, handle: int) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/close", json_body={"handle": handle})

    async def upload_large_file(
        self, path: str, base64_chunks: list[str], overwrite: bool = True
    ) -> dict[str, Any]:
        """Upload a large file via the streaming create/add-block/close flow."""
        created = await self.create(path, overwrite)
        handle = created["handle"]
        for chunk in base64_chunks:
            await self.add_block(handle, chunk)
        await self.close(handle)
        return {"path": path, "handle": handle, "chunks": len(base64_chunks), "uploaded": True}

    async def download_file(self, path: str, chunk_size: int = 1024 * 1024) -> dict[str, Any]:
        """Download a (potentially large) file by paging through /read."""
        status = await self.get_status(path)
        file_size = status.get("file_size", 0)
        offset = 0
        chunks: list[str] = []
        while offset < file_size:
            page = await self.read(path, offset, chunk_size)
            data = page.get("data", "")
            chunks.append(data)
            bytes_read = page.get("bytes_read", 0)
            if bytes_read == 0:
                break
            offset += bytes_read
        return {"path": path, "file_size": file_size, "chunks": chunks}
