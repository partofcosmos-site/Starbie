#!/usr/bin/env python3
"""
Starbie Sovereign Session Recorder & Timelapse Engine
=====================================================
Automated video documentation and maker proof for Hack Club Half Life.
Supports:
1. Desktop Timelapse Daemon (Continuous background frames via Windows-MCP, compiled with FFmpeg).
2. Ghost-Mode Browser Recording (Headless 1080p portal, GitHub repo, and HTML simulator tour via CDP).
3. On-demand video compilation and status inspection.
"""

import os
import sys
import time
import json
import base64
import asyncio
import argparse
import subprocess
import urllib.request

STARBIE_DIR = r"C:\Users\white\Starbie"
RECORDINGS_DIR = os.path.join(STARBIE_DIR, "recordings")
FRAMES_DIR = os.path.join(RECORDINGS_DIR, "frames")
STATUS_FILE = os.path.join(RECORDINGS_DIR, "timelapse_status.json")
STOP_FILE = os.path.join(RECORDINGS_DIR, "stop.signal")
DEFAULT_VIDEO = os.path.join(RECORDINGS_DIR, "starbie_maker_timelapse.mp4")
GHOST_VIDEO = os.path.join(RECORDINGS_DIR, "starbie_ghost_proof.mp4")
FFMPEG = r"C:\Users\white\.local\bin\ffmpeg.exe"
PYTHON_VENV = r"C:\Users\white\AppData\Roaming\uv\tools\windows-mcp\Scripts\python.exe"
CDP_JSON_URL = "http://127.0.0.1:9100/json"
WINDOWS_MCP_SSE = "http://127.0.0.1:8000/sse"

os.makedirs(FRAMES_DIR, exist_ok=True)

def get_next_frame_index(frames_dir):
    existing = [f for f in os.listdir(frames_dir) if f.startswith("frame_") and f.endswith(".png")]
    if not existing:
        return 0
    indices = []
    for f in existing:
        try:
            idx = int(f.replace("frame_", "").replace(".png", ""))
            indices.append(idx)
        except ValueError:
            pass
    return max(indices) + 1 if indices else 0

async def capture_desktop_frame_mcp():
    """Captures an interactive desktop frame via Windows-MCP SSE without focus theft."""
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        async with sse_client(WINDOWS_MCP_SSE) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool("Screenshot", {})
                for item in res.content:
                    if hasattr(item, "data") and item.data:
                        return base64.b64decode(item.data)
    except Exception as e:
        return None
    return None

def compile_frames_to_video(frames_dir=FRAMES_DIR, output_video=DEFAULT_VIDEO, framerate=24):
    """Compiles captured PNG frames into a compressed H.264 MP4."""
    frames = [f for f in os.listdir(frames_dir) if f.startswith("frame_") and f.endswith(".png")]
    if not frames:
        return False, "No frames found to compile."
    
    # Sort and re-index sequentially if gaps exist
    frames.sort()
    temp_dir = os.path.join(RECORDINGS_DIR, "seq_frames")
    os.makedirs(temp_dir, exist_ok=True)
    for f in os.listdir(temp_dir):
        try:
            os.remove(os.path.join(temp_dir, f))
        except Exception:
            pass

    for seq_idx, f_name in enumerate(frames):
        src = os.path.join(frames_dir, f_name)
        dst = os.path.join(temp_dir, f"seq_{seq_idx:05d}.png")
        try:
            if hasattr(os, "link"):
                os.link(src, dst)
            else:
                import shutil
                shutil.copyfile(src, dst)
        except Exception:
            import shutil
            shutil.copyfile(src, dst)

    cmd = [
        FFMPEG,
        "-y",
        "-framerate", str(framerate),
        "-i", os.path.join(temp_dir, "seq_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "fast",
        output_video
    ]
    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        size_mb = os.path.getsize(output_video) / (1024 * 1024)
        return True, f"Video compiled successfully: {output_video} ({size_mb:.2f} MB, {len(frames)} frames)"
    except Exception as e:
        return False, f"FFmpeg compilation failed: {e}"

def run_worker(interval=2.0, max_frames=None):
    """Background worker loop capturing frames periodically."""
    if os.path.exists(STOP_FILE):
        try:
            os.remove(STOP_FILE)
        except Exception:
            pass

    start_time = time.time()
    pid = os.getpid()
    status_data = {
        "pid": pid,
        "status": "recording",
        "start_time": start_time,
        "interval": interval,
        "frames_captured": 0,
        "last_frame_time": start_time
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f, indent=2)

    frame_idx = get_next_frame_index(FRAMES_DIR)
    frames_recorded_this_run = 0

    try:
        while True:
            if os.path.exists(STOP_FILE):
                break
            
            t0 = time.time()
            img_bytes = asyncio.run(capture_desktop_frame_mcp())
            if img_bytes:
                frame_path = os.path.join(FRAMES_DIR, f"frame_{frame_idx:05d}.png")
                with open(frame_path, "wb") as f:
                    f.write(img_bytes)
                frame_idx += 1
                frames_recorded_this_run += 1
                
                status_data["frames_captured"] = frames_recorded_this_run
                status_data["last_frame_time"] = time.time()
                status_data["total_frames_in_dir"] = frame_idx
                with open(STATUS_FILE, "w") as f:
                    json.dump(status_data, f, indent=2)

            if max_frames and frames_recorded_this_run >= max_frames:
                break

            elapsed = time.time() - t0
            sleep_time = max(0.1, interval - elapsed)
            time.sleep(sleep_time)

    finally:
        status_data["status"] = "stopped"
        status_data["end_time"] = time.time()
        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=2)
        
        # Auto compile
        compile_frames_to_video(FRAMES_DIR, DEFAULT_VIDEO, framerate=24)
        if os.path.exists(STOP_FILE):
            try:
                os.remove(STOP_FILE)
            except Exception:
                pass

def start_timelapse(interval=2.0):
    """Starts the timelapse daemon in the background."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                st = json.load(f)
            if st.get("status") == "recording":
                # Check if PID is still alive
                pid = st.get("pid")
                if pid:
                    res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
                    if str(pid) in res.stdout:
                        return f"Timelapse daemon is already active (PID {pid}, {st.get('frames_captured', 0)} frames recorded)."
        except Exception:
            pass

    if os.path.exists(STOP_FILE):
        try:
            os.remove(STOP_FILE)
        except Exception:
            pass

    cmd = [
        PYTHON_VENV,
        os.path.abspath(__file__),
        "worker",
        "--interval", str(interval)
    ]
    # Launch detached
    subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1.0)
    return f"Started background maker timelapse daemon (Interval: {interval}s). Frames saving to {FRAMES_DIR}."

def stop_timelapse():
    """Signals the daemon to stop and compile the MP4."""
    with open(STOP_FILE, "w") as f:
        f.write("stop")
    time.sleep(2.5)
    
    # Check status
    st = {}
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            st = json.load(f)
    
    success, msg = compile_frames_to_video(FRAMES_DIR, DEFAULT_VIDEO, framerate=24)
    return f"Timelapse stopped. {msg}"

def get_status():
    """Reports status of timelapse recording."""
    if not os.path.exists(STATUS_FILE):
        frames_count = len([f for f in os.listdir(FRAMES_DIR) if f.startswith("frame_") and f.endswith(".png")])
        video_exists = os.path.exists(DEFAULT_VIDEO)
        video_size = os.path.getsize(DEFAULT_VIDEO) / (1024*1024) if video_exists else 0
        return {
            "status": "idle",
            "frames_on_disk": frames_count,
            "compiled_video": DEFAULT_VIDEO if video_exists else None,
            "video_size_mb": round(video_size, 2)
        }
    with open(STATUS_FILE, "r") as f:
        data = json.load(f)
    frames_count = len([f for f in os.listdir(FRAMES_DIR) if f.startswith("frame_") and f.endswith(".png")])
    data["frames_on_disk"] = frames_count
    if os.path.exists(DEFAULT_VIDEO):
        data["compiled_video"] = DEFAULT_VIDEO
        data["video_size_mb"] = round(os.path.getsize(DEFAULT_VIDEO) / (1024 * 1024), 2)
    return data

async def record_ghost_tour():
    """Records an authentic Ghost-Mode proof tour of Half-Life portal + Starbie repo + simulator."""
    import websockets
    ghost_frames_dir = os.path.join(RECORDINGS_DIR, "ghost_frames")
    os.makedirs(ghost_frames_dir, exist_ok=True)
    for f in os.listdir(ghost_frames_dir):
        if f.endswith(".png"):
            try:
                os.remove(os.path.join(ghost_frames_dir, f))
            except Exception:
                pass

    frame_counter = 0

    # 1. Capture Half-Life Tab
    with urllib.request.urlopen(CDP_JSON_URL, timeout=5) as resp:
        tabs = json.loads(resp.read().decode())
    
    portal_tab = next((t for t in tabs if "cmuvlli9601rm01py0u6opf9x" in t.get("url", "") or "Starbie" in t.get("title", "")), None)
    if not portal_tab:
        portal_tab = next((t for t in tabs if "halflife" in t.get("url", "")), None)

    if portal_tab:
        ws_url = portal_tab["webSocketDebuggerUrl"]
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            await ws.send(json.dumps({
                "id": 1,
                "method": "Emulation.setDeviceMetricsOverride",
                "params": {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False}
            }))
            await ws.recv()
            await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": "window.scrollTo(0, 0);"}}))
            await ws.recv()
            await asyncio.sleep(0.5)

            # Scroll through portal
            for y in range(0, 2400, 75):
                await ws.send(json.dumps({
                    "id": 10,
                    "method": "Runtime.evaluate",
                    "params": {"expression": f"window.scrollTo({{ top: {y}, behavior: 'instant' }});"}
                }))
                await ws.recv()
                await asyncio.sleep(0.06)
                
                # Capture frame
                msg = {"id": 1000 + frame_counter, "method": "Page.captureScreenshot", "params": {"format": "png"}}
                await ws.send(json.dumps(msg))
                res = json.loads(await ws.recv())
                data = res.get("result", {}).get("data")
                if data:
                    with open(os.path.join(ghost_frames_dir, f"frame_{frame_counter:05d}.png"), "wb") as pf:
                        pf.write(base64.b64decode(data))
                    frame_counter += 1

    # 2. Simulator Tab
    sim_path = "file:///" + os.path.abspath(os.path.join(STARBIE_DIR, "Firmware", "simulator.html")).replace("\\", "/")
    req = urllib.request.Request(f"{CDP_JSON_URL}/new?{sim_path}", method="PUT")
    with urllib.request.urlopen(req) as resp:
        sim_tab = json.loads(resp.read().decode())
    sim_id = sim_tab["id"]
    sim_ws = sim_tab["webSocketDebuggerUrl"]

    try:
        async with websockets.connect(sim_ws, max_size=50*1024*1024) as ws_sim:
            await ws_sim.send(json.dumps({
                "id": 1,
                "method": "Emulation.setDeviceMetricsOverride",
                "params": {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False}
            }))
            await ws_sim.recv()
            await asyncio.sleep(1.5)

            # Simulate interactive events (shake, button presses, temperature change)
            for _ in range(15):
                msg = {"id": 2000 + frame_counter, "method": "Page.captureScreenshot", "params": {"format": "png"}}
                await ws_sim.send(json.dumps(msg))
                res = json.loads(await ws_sim.recv())
                data = res.get("result", {}).get("data")
                if data:
                    with open(os.path.join(ghost_frames_dir, f"frame_{frame_counter:05d}.png"), "wb") as pf:
                        pf.write(base64.b64decode(data))
                    frame_counter += 1
                await asyncio.sleep(0.05)

            # Click Button 1 in simulator
            await ws_sim.send(json.dumps({
                "id": 20,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.getElementById('buttonOne').click();"}
            }))
            await ws_sim.recv()
            await asyncio.sleep(0.5)

            for _ in range(15):
                msg = {"id": 2020 + frame_counter, "method": "Page.captureScreenshot", "params": {"format": "png"}}
                await ws_sim.send(json.dumps(msg))
                res = json.loads(await ws_sim.recv())
                data = res.get("result", {}).get("data")
                if data:
                    with open(os.path.join(ghost_frames_dir, f"frame_{frame_counter:05d}.png"), "wb") as pf:
                        pf.write(base64.b64decode(data))
                    frame_counter += 1
                await asyncio.sleep(0.05)

    finally:
        try:
            close_req = urllib.request.Request(f"{CDP_JSON_URL}/close/{sim_id}", method="PUT")
            urllib.request.urlopen(close_req)
        except Exception:
            pass

    # Compile ghost video
    compile_frames_to_video(ghost_frames_dir, GHOST_VIDEO, framerate=24)
    size_mb = os.path.getsize(GHOST_VIDEO) / (1024*1024) if os.path.exists(GHOST_VIDEO) else 0
    return f"Ghost proof video created: {GHOST_VIDEO} ({size_mb:.2f} MB, {frame_counter} frames)"

def main():
    parser = argparse.ArgumentParser(description="Starbie Session Recorder & Timelapse Engine")
    parser.add_argument("action", choices=["start", "stop", "status", "compile", "worker", "ghost-portal", "snap"])
    parser.add_argument("--interval", type=float, default=2.0, help="Interval in seconds between frames")
    parser.add_argument("--max-frames", type=int, default=None, help="Max frames for worker")
    args = parser.parse_args()

    if args.action == "start":
        print(start_timelapse(args.interval))
    elif args.action == "stop":
        print(stop_timelapse())
    elif args.action == "status":
        print(json.dumps(get_status(), indent=2))
    elif args.action == "compile":
        success, msg = compile_frames_to_video(FRAMES_DIR, DEFAULT_VIDEO, framerate=24)
        print(msg)
    elif args.action == "worker":
        run_worker(args.interval, args.max_frames)
    elif args.action == "ghost-portal":
        print(asyncio.run(record_ghost_tour()))
    elif args.action == "snap":
        img = asyncio.run(capture_desktop_frame_mcp())
        if img:
            idx = get_next_frame_index(FRAMES_DIR)
            path = os.path.join(FRAMES_DIR, f"frame_{idx:05d}.png")
            with open(path, "wb") as f:
                f.write(img)
            print(f"Captured single frame to {path}")
        else:
            print("Failed to capture frame")

if __name__ == "__main__":
    main()
