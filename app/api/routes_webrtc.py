from fastapi import APIRouter, Depends, HTTPException
from aiortc import RTCPeerConnection, RTCSessionDescription

from app.schemas import WebRTCOffer, WebRTCAnswer
from app.runtime.video_track import CounterVideoTrack
from app.infrastructure.logging.json_logger import logger
from app.security.auth import AuthenticatedUser, require_authenticated_user


def create_webrtc_router(counter, pcs: set):
    router = APIRouter()

    @router.post("/webrtc-offer", response_model=WebRTCAnswer)
    async def webrtc_offer(
        offer: WebRTCOffer,
        _: AuthenticatedUser = Depends(require_authenticated_user),
    ):
        if not counter.supports_video():
            logger.error(
                "当前模式不支持视频流，拒绝 WebRTC 建连",
                extra={"event": "api_webrtc_not_supported"}
            )
            raise HTTPException(
                status_code=400,
                detail="Current mode does not support video streaming."
            )

        pc = RTCPeerConnection()
        pcs.add(pc)

        logger.info(
            f"创建新的 WebRTC PeerConnection，当前连接数={len(pcs)}",
            extra={"event": "api_webrtc_connection_created"}
        )

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(
                f"WebRTC 连接状态变化: {pc.connectionState}",
                extra={"event": "api_webrtc_connection_state_changed"}
            )

            if pc.connectionState in ("failed", "closed", "disconnected"):
                await pc.close()
                pcs.discard(pc)

                logger.info(
                    f"WebRTC 连接已关闭并移除，当前连接数={len(pcs)}",
                    extra={"event": "api_webrtc_connection_closed"}
                )

        video_track = CounterVideoTrack(counter)
        pc.addTrack(video_track)

        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=offer.sdp, type=offer.type)
        )

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        logger.info(
            "WebRTC answer 创建成功",
            extra={"event": "api_webrtc_answer_created"}
        )

        return WebRTCAnswer(
            sdp=pc.localDescription.sdp,
            type=pc.localDescription.type
        )

    return router
