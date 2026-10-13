from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.stream import Stream
from app.services.token_service import verify_stream_token
from app.utils.ssrf_guard import is_safe_url
import httpx

router = APIRouter(tags=["Stream Proxy"])

@router.get("/stream/{stream_id}")
async def proxy_audio_stream(
    stream_id: int,
    t: str = Query(..., description="Signed HMAC access token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Secure Audio Proxy endpoint.
    - Validates expiring HMAC token
    - Verifies stream existence in database
    - Enforces SSRF defense (no internal IP/metadata access)
    - Adds necessary CORS headers
    """
    if not verify_stream_token(stream_id, t):
        raise HTTPException(status_code=403, detail="Invalid or expired stream token")

    stream_res = await db.execute(select(Stream).where(Stream.id == stream_id))
    stream = stream_res.scalar_one_or_none()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    target_url = stream.url_resolved or stream.url
    if not is_safe_url(target_url):
        raise HTTPException(status_code=400, detail="Disallowed or unsafe upstream URL")

    # Connect to upstream stream with httpx streaming response
    client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=None), follow_redirects=True)
    
    try:
        upstream_req = client.build_request(
            "GET",
            target_url,
            headers={
                "User-Agent": "RadioGlobe/1.0",
                "Icy-MetaData": "1"
            }
        )
        upstream_res = await client.send(upstream_req, stream=True)
    except Exception as e:
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"Failed to connect to station: {str(e)}")

    content_type = upstream_res.headers.get("content-type", "audio/mpeg")

    async def stream_generator():
        try:
            async for chunk in upstream_res.aiter_bytes(chunk_size=8192):
                yield chunk
        finally:
            await upstream_res.aclose()
            await client.aclose()

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    return StreamingResponse(
        stream_generator(),
        media_type=content_type,
        headers=headers
    )
