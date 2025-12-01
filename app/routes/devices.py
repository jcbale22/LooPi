# app/routes/devices.py

from fastapi import APIRouter, Request, Form, Depends, Query, Cookie, status
from fastapi.responses import RedirectResponse, HTMLResponse
from app.utils.context_helpers import inject_user_context
from app.models.device_model import Device
from app.services.device_service import (
    load_devices as get_devices,
    save_devices as save_device,
)
from app.services.playlist_service import (
    load_playlists,
    save_playlists,
    sync_playlists_to_state,
    update_playlist_device_assignments
)
from uuid import uuid4
from datetime import datetime, timedelta

router = APIRouter()

# === CONSTANTS ===
TOKEN_ROTATION_THRESHOLD = timedelta(days=7)
DEVICE_EXPIRATION_THRESHOLD = timedelta(days=30)

# === DEVICE MANAGEMENT PAGE ===
@router.get("/devices")
async def devices_page(request: Request):
    context = inject_user_context(request)
    raw_devices = get_devices()
    devices_with_days = {}

    for device_id, info in raw_devices.items():
        device = info.copy()
        if "last_seen" in device:
            try:
                last_seen = datetime.fromisoformat(device["last_seen"])
                days_left = (last_seen + DEVICE_EXPIRATION_THRESHOLD - datetime.utcnow()).days
                device["days_left"] = max(days_left, 0)
            except Exception:
                device["days_left"] = None
        else:
            device["days_left"] = None
        devices_with_days[device_id] = device

    sorted_devices = dict(
        sorted(
            devices_with_days.items(),
            key=lambda item: not item[1].get("active", False)
        )
    )

    context["devices"] = sorted_devices
    context["playlists"] = request.app.state.playlists
    return request.app.templates.TemplateResponse("devices.html", context)

# === DEVICE CREATE / UPDATE (NAME, PLAYLIST) ===
@router.post("/devices/update")
async def update_device(
    request: Request,
    device_id: str = Form(...),
    name: str = Form(""),
    active_playlist: str = Form(""),
    original_device_id: str = Form(None)
):
    devices = get_devices()
    now = datetime.utcnow().isoformat()

    device_key = original_device_id if original_device_id and original_device_id in devices else device_id

    if device_key in devices:
        if device_id != device_key:
            devices[device_id] = devices.pop(device_key)
            device_key = device_id

        devices[device_key]["name"] = name
        devices[device_key]["active_playlist"] = active_playlist
        devices[device_key]["last_seen"] = now
    else:
        devices[device_id] = {
            "name": name,
            "active_playlist": active_playlist,
            "auth_token": str(uuid4()),
            "last_seen": now,
            "active": False
        }

    save_device(devices)
    update_playlist_device_assignments(devices)
    return RedirectResponse(url="/devices", status_code=303)

# === ROTATE AUTH TOKEN FOR DEVICE ===
@router.post("/devices/{device_id}/rotate_token")
async def rotate_token(device_id: str):
    devices = get_devices()
    if device_id in devices:
        devices[device_id]["auth_token"] = str(uuid4())
        save_device(devices)
        return {"success": True, "new_token": devices[device_id]["auth_token"]}
    return {"error": "Device not found"}

# === MARK THIS DEVICE AS ACTIVE ===
@router.post("/devices/mark")
async def mark_this_device(request: Request, device_id: str = Form(...)):
    devices = get_devices()
    if device_id in devices:
        active_devices = [d for d in devices.values() if d.get("active")]
        device_limit = request.user.subscription.device_limit if hasattr(request.user, "subscription") else 1

        if len(active_devices) < device_limit or devices[device_id].get("active"):
            devices[device_id]["active"] = True
            for key, dev in devices.items():
                if key != device_id:
                    dev["active"] = False
            save_device(devices)
            update_playlist_device_assignments(devices)
        else:
            context = inject_user_context({"request": request})
            context["error"] = f"You've reached your limit of {device_limit} active devices."
            context["devices"] = devices
            context["playlists"] = request.app.state.playlists
            return request.app.templates.TemplateResponse("claim_denied.html", context)

    return RedirectResponse(url="/devices", status_code=303)

# === CLAIM DEVICE VIA QR OR LINK ===
@router.get("/claim", response_class=HTMLResponse)
async def claim_device(request: Request, device_id: str = Query(...), auth_token: str = Query(...)):
    devices = get_devices()
    device = devices.get(device_id)

    if not device or device.get("auth_token") != auth_token:
        return HTMLResponse("<h3>Unauthorized device or invalid token.</h3>", status_code=403)

    active_devices = [d for d in devices.values() if d.get("active")]
    device_limit = request.user.subscription.device_limit if hasattr(request.user, "subscription") else 1

    if len(active_devices) >= device_limit and not device.get("active"):
        return HTMLResponse(f"<h3>Device limit exceeded ({device_limit}).</h3>", status_code=403)

    for key in devices:
        devices[key]["active"] = (key == device_id)

    save_device(devices)
    update_playlist_device_assignments(devices)

    response = RedirectResponse(url=f"/display?device_id={device_id}", status_code=303)
    response.set_cookie("loopi_device_id", device_id, max_age=60*60*24*365, path="/")
    response.set_cookie("loopi_device_token", device["auth_token"], max_age=60*60*24*365, path="/")
    return response

# === FALLBACK WHEN CLAIM NEEDED ===
@router.get("/claim-needed", response_class=HTMLResponse)
async def claim_needed(request: Request):
    context = inject_user_context({"request": request})
    context["message"] = "This device isn't registered or authorized. Please scan a claim QR code or visit the Devices page."
    return request.app.templates.TemplateResponse("claim_needed.html", context)

# === LOOPI DISPLAY ENDPOINT (SECURED BY COOKIE TOKEN) ===
@router.get("/display", response_class=HTMLResponse)
async def display_screen(
    request: Request,
    device_id: str = Query(None),
    token_cookie: str = Cookie(None, alias="loopi_device_token"),
    id_cookie: str = Cookie(None, alias="loopi_device_id")
):
    device_id = device_id or id_cookie
    if not device_id or not token_cookie:
        return RedirectResponse(url="/claim-needed", status_code=303)

    devices = get_devices()
    device = devices.get(device_id)

    if not device or device.get("auth_token") != token_cookie or not device.get("active"):
        return RedirectResponse(url="/claim-needed", status_code=303)

    context = inject_user_context({"request": request})
    context["device"] = device
    return request.app.templates.TemplateResponse("display.html", context)

# === DEVICE HEARTBEAT ENDPOINT ===
@router.post("/devices/heartbeat")
async def device_heartbeat(
    device_id: str = Form(...),
    auth_token: str = Form(...)
):
    devices = get_devices()
    device = devices.get(device_id)

    if not device or device.get("auth_token") != auth_token:
        return {"status": "error", "message": "Invalid device or token"}, status.HTTP_403_FORBIDDEN

    now = datetime.utcnow()
    device["last_seen"] = now.isoformat()

    try:
        last_seen_dt = datetime.fromisoformat(device["last_seen"])
        if now - last_seen_dt > DEVICE_EXPIRATION_THRESHOLD:
            device["active"] = False
        elif now - last_seen_dt > TOKEN_ROTATION_THRESHOLD:
            device["auth_token"] = str(uuid4())
    except Exception:
        pass

    save_device(devices)
    update_playlist_device_assignments(devices)
    return {"status": "ok"}
