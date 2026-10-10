"""The one public door to private storage: GET /files/{key}?exp=...&sig=..."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from . import storage

router = APIRouter(tags=["Files"])


@router.get("/files/{key:path}", include_in_schema=False)
def get_file(key: str, exp: str = Query(""), sig: str = Query("")) -> FileResponse:
    """Serve a stored file when the link is genuine and has not expired.

    403 for a link that was changed or forged, 410 for an expired one, 404 when the file is gone.
    """
    try:
        storage.verify(key, exp, sig)
        path, content_type = storage.locate(key)
    except storage.StorageError as err:
        raise HTTPException(err.status_code, str(err)) from None
    return FileResponse(
        path, media_type=content_type,
        headers={
            "Cache-Control": "private, no-store",          # a saved copy must not outlive the link
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
            "Referrer-Policy": "no-referrer",
            "Content-Disposition": "inline",
        },
    )
