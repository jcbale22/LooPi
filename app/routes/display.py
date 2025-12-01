# app/routes/display.py

from fastapi import APIRouter, Request, Form, Query, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from uuid import uuid4
from datetime import datetime, timedelta

from app.utils.context_helpers import inject_user_context
from app.services.device_service import (
    load_devices as get_devices,
    save_devices as save_device,
)
from app.models.device_model import Device

router = APIRouter()

# === DEVICE MANAGEMENT PAGE ===
@router.get("/devices")
async def devices_page(request: Request):
    # Inject user context
    context = inject_user_context(request)
    raw_devices = get_devices()

    devices_with_days = {}
    for device_id, info in raw_devices.items():
        device = info.copy()
        # Calculate days_left from last_seen or set to None
        if "last_seen" in device:
            try:
                last_seen = datetime.fromisoformat(device["last_seen"])
                days_left = (last_seen + timedelta(days=30) - datetime.utcnow()).days
                device["days_left"] = max(days_left, 0)
            except Exception:
                device["days_left"] = None
        else:
            device["days_left"] = None
        devices_with_days[device_id] = device

    # Add to template context
    context["devices"] = devices_with_days
    context["playlists"] = request.app.state.playlists
    return request.app.templates.TemplateResponse("devices.html", context)

# === REGISTER OR UPDATE DEVICE ===
@router.post("/devices/update")
async def update_device(
    request: Request,
    device_id: str = Form(...),
    name: str = Form(""),
    active_playlist: str = Form("")
):
    devices = get_devices()
    now = datetime.utcnow().isoformat()

    if device_id in devices:
        # Update existing device
        devices[device_id]["name"] = name
        devices[device_id]["active_playlist"] = active_playlist
        devices[device_id]["last_seen"] = now
    else:
        # Register new device
        devices[device_id] = {
            "name": name,
            "active_playlist": active_playlist,
            "auth_token": str(uuid4()),
            "active": False,
            "last_seen": now
        }

    save_device(devices)
    return RedirectResponse(url="/devices", status_code=303)

# === ROTATE AUTH TOKEN ===
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
            # Mark target device as active and others as inactive
            devices[device_id]["active"] = True
            for key, dev in devices.items():
                if key != device_id:
                    dev["active"] = False
            save_device(devices)
        else:
            # Render error if limit exceeded
            context = inject_user_context(request)
            context["error"] = f"You've reached your limit of {device_limit} active devices. Please deactivate another device or upgrade your subscription."
            context["devices"] = devices
            context["playlists"] = request.app.state.playlists
            return request.app.templates.TemplateResponse("claim_denied.html", context)

    return RedirectResponse(url="/devices", status_code=303)

# === CLAIM DEVICE (VIA QR OR LINK) ===
@router.get("/claim", response_class=HTMLResponse)
async def claim_device(request: Request, device_id: str = Query(...), auth_token: str = Query(...)):
    devices = get_devices()
    device = devices.get(device_id)

    # Validate token
    if not device or device.get("auth_token") != auth_token:
        return HTMLResponse("<h3>Unauthorized device or invalid token.</h3>", status_code=403)

    # Enforce license limit
    active_devices = [d for d in devices.values() if d.get("active")]
    device_limit = request.user.subscription.device_limit if hasattr(request.user, "subscription") else 1
    if len(active_devices) >= device_limit and not device.get("active"):
        return HTMLResponse(f"<h3>Device limit exceeded ({device_limit}). Please deactivate another device.</h3>", status_code=403)

    # Activate claimed device only
    for key in devices:
        devices[key]["active"] = (key == device_id)

    save_device(devices)

    # Set cookies for device tracking
    response = RedirectResponse(url=f"/display?device_id={device_id}", status_code=303)
    response.set_cookie("loopi_device_id", device_id, max_age=60*60*24*365, path="/")
    response.set_cookie("loopi_device_token", device["auth_token"], max_age=60*60*24*365, path="/")
    return response

# === CLAIM FALLBACK PAGE ===
@router.get("/claim-needed", response_class=HTMLResponse)
async def claim_needed(request: Request):
    context = inject_user_context(request)
    context["message"] = "This device isn't registered or authorized. Please scan a claim QR code or visit the Devices page."
    return request.app.templates.TemplateResponse("claim_needed.html", context)

# === DISPLAY ENDPOINT (COOKIE-SECURED) ===
@router.get("/display", response_class=HTMLResponse)
async def display_screen(
    request: Request,
    device_id: str = Query(None),
    token_cookie: str = Cookie(None, alias="loopi_device_token"),
    id_cookie: str = Cookie(None, alias="loopi_device_id")
):
    # Use query param or fallback to cookie
    device_id = device_id or id_cookie
    if not device_id or not token_cookie:
        return RedirectResponse(url="/claim-needed", status_code=303)

    devices = get_devices()
    device = devices.get(device_id)

    # Reject if token mismatch or inactive
    if not device or device.get("auth_token") != token_cookie or not device.get("active"):
        return RedirectResponse(url="/claim-needed", status_code=303)

    # Valid device → render display
    context = inject_user_context(request)
    context["device"] = device
    return request.app.templates.TemplateResponse("display.html", context)