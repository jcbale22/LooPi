# app/scripts/test_display_auth.py

import argparse
import requests
from rich import print
from rich.console import Console

console = Console()

BASE_URL = "http://127.0.0.1:8000"

def test_display_auth(device_id: str, token: str):
    url = f"{BASE_URL}/display?device_id={device_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        status = response.status_code

        if status == 200:
            print(f"[green]✅ Device '{device_id}' authenticated successfully. HTTP {status}[/green]")
        elif status == 403:
            print(f"[red]❌ Unauthorized: Token was invalid for device '{device_id}'. HTTP 403[/red]")
        elif status == 404:
            print(f"[yellow]⚠ Device ID '{device_id}' not found. HTTP 404[/yellow]")
        else:
            print(f"[orange1]Unexpected response: HTTP {status}[/orange1]")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("[bold red]🚫 Connection failed. Is the FastAPI server running at localhost:8000?[/bold red]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test /display endpoint device authentication")
    parser.add_argument("--device", required=True, help="Device ID to test")
    parser.add_argument("--token", required=True, help="Auth token to use")

    args = parser.parse_args()
    test_display_auth(args.device, args.token)
