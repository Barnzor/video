#!/usr/bin/env python3
"""
OpenRouter studio: make videos and images through OpenRouter from the command line.

Standard library only. Reads the key from OPENROUTER_API_KEY.

  studio.py credits                                  account balance (free)
  studio.py models video|image [--search TEXT]       live model list with options and prices (free)
  studio.py quote --model M --duration 5 --resolution 720p [--audio] [--image-input]
  studio.py video --model M --prompt "..." [options]  make a video, wait, download
  studio.py image --model M --prompt "..." [options]  make one or more images
  studio.py wait JOB_ID                              resume waiting for a video job
  studio.py history [--last 10]                      what was made, with cost

Run any command with -h for its options. Files go to ./outputs unless --out-dir says otherwise.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://openrouter.ai/api/v1"
DEFAULT_OUT = Path(os.environ.get("STUDIO_OUT_DIR", "outputs"))
FPS_GUESS = 24  # used only to estimate token-priced (Seedance) videos


# ----------------------------------------------------------------------------- http

def _key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set. Save it in the environment settings, then try again.")
    return key


def call(method: str, path: str, body: dict | None = None, auth: bool = True, raw: bool = False):
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {"Content-Type": "application/json", "X-Title": "openrouter-studio"}
    if auth:
        headers["Authorization"] = f"Bearer {_key()}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            payload = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:2000]
        if "zdr-violation" in detail or "ZDR violation" in detail:
            sys.exit("BLOCKED BY ACCOUNT PRIVACY SETTING: the OpenRouter account only allows Zero Data Retention "
                     "providers, and no provider for this model offers that (no video model does). Nothing was charged. "
                     "The account owner can change it at https://openrouter.ai/settings/privacy "
                     "(turn off 'ZDR endpoints only', or allow it just for this key if that option is offered).")
        if e.code == 402:
            sys.exit("Not enough OpenRouter credit for this. Top up at https://openrouter.ai/settings/credits")
        sys.exit(f"OpenRouter said {e.code} for {method} {path}:\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach OpenRouter: {e.reason}")
    return payload if raw else json.loads(payload)


# ---------------------------------------------------------------------------- utils

def media_ref(src: str) -> str:
    """A URL is passed through; a local file becomes a base64 data URL."""
    if re.match(r"^(https?:|data:)", src):
        return src
    p = Path(src).expanduser()
    if not p.is_file():
        sys.exit(f"No such file: {src}")
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:n].rstrip("-")) or "untitled"


def out_path(out_dir: Path, prompt: str, ext: str, name: str | None, index: int | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = name or f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{slug(prompt)}"
    if index is not None:
        base = f"{base}-{index + 1}"
    p = out_dir / f"{base}{ext}"
    i = 2
    while p.exists():
        p = out_dir / f"{base}-v{i}{ext}"
        i += 1
    return p


def log(out_dir: Path, entry: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    entry = {"at": dt.datetime.now().isoformat(timespec="seconds"), **entry}
    with open(out_dir / "history.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


def money(x) -> str:
    return "unknown" if x is None else f"${float(x):.3f}"


def find_model(kind: str, model_id: str) -> dict:
    data = call("GET", f"/{'videos' if kind == 'video' else 'images'}/models", auth=False)["data"]
    for m in data:
        if m["id"] == model_id:
            return m
    close = [m["id"] for m in data if model_id.split("/")[-1].split("-")[0] in m["id"]][:8]
    sys.exit(f"No {kind} model called {model_id}." + (f" Close matches: {', '.join(close)}" if close else ""))


# --------------------------------------------------------------------------- pricing

RES_PIXELS = {"360p": (640, 360), "480p": (854, 480), "720p": (1280, 720), "768p": (1366, 768),
              "1080p": (1920, 1080), "1K": (1920, 1080), "2K": (2560, 1440), "4K": (3840, 2160)}


def estimate_video(m: dict, duration: int, resolution: str | None, audio: bool, image_input: bool) -> tuple[float | None, str]:
    """Best-effort USD estimate from the model's pricing SKUs. Returns (usd, which sku was used)."""
    skus = {k: float(v) for k, v in (m.get("pricing_skus") or {}).items()}
    if not skus:
        return None, "no price listed"
    res = (resolution or "").lower()
    secs = max(duration, 1)

    def pick(cands: list[str]) -> str | None:
        # Most specific first: right mode, right audio, right resolution.
        def score(k: str) -> int:
            s = 0
            if res and k.endswith("_" + res):
                s += 4
            elif re.search(r"_(\d+p|\dk)$", k):
                s -= 10  # a different resolution's price
            if ("without_audio" in k) == (not audio):
                s += 2
            if "with_audio" in k and not audio:
                s -= 5
            if k.startswith("image_to_video") and image_input:
                s += 3
            if k.startswith("text_to_video") and not image_input:
                s += 3
            if k.startswith(("image_to_video", "text_to_video")) and not k.startswith("image_to_video" if image_input else "text_to_video"):
                s -= 10
            for bad in ("long_", "reference", "continuation", "with_video_input", "minimum", "image_input", "megapixel"):
                if bad in k:
                    s -= 20
            return s
        cands = sorted(cands, key=score, reverse=True)
        return cands[0] if cands and score(cands[0]) > -10 else None

    extra = 0.0
    if image_input and "cents_per_image_input" in skus:
        extra += skus["cents_per_image_input"] / 100

    per_sec = [k for k in skus if "duration_seconds" in k]
    cents = [k for k in skus if k.startswith("cents_per") and "second" in k and "megapixel" not in k]
    tokens = [k for k in skus if k.startswith("video_tokens")]
    usd = None
    used = ""
    if per_sec and (k := pick(per_sec)):
        usd, used = skus[k] * secs, k
    elif cents and (k := pick(cents)):
        usd, used = skus[k] / 100 * secs, k
    elif tokens and (k := pick(tokens)):
        w, h = RES_PIXELS.get(resolution or "720p", (1280, 720))
        usd, used = skus[k] * (w * h * FPS_GUESS * secs / 1024), f"{k} (token count estimated)"
    if usd is None:
        return None, "could not match a price; see pricing_skus"
    if "minimum_cents_per_generation" in skus:
        usd = max(usd, skus["minimum_cents_per_generation"] / 100)
    return round(usd + extra, 4), used


# -------------------------------------------------------------------------- commands

def cmd_credits(_):
    d = call("GET", "/credits")["data"]
    left = d["total_credits"] - d["total_usage"]
    print(f"Balance: ${left:.2f} left (bought ${d['total_credits']:.2f}, used ${d['total_usage']:.2f})")


def cmd_models(a):
    kind = a.kind
    data = call("GET", f"/{'videos' if kind == 'video' else 'images'}/models", auth=False)["data"]
    if a.search:
        q = a.search.lower()
        data = [m for m in data if q in m["id"].lower() or q in (m.get("description") or "").lower()]
    for m in data:
        print(f"## {m['id']}  ({m.get('name', '')})")
        if a.long:
            print(f"   {(m.get('description') or '').strip()}")
        if kind == "video":
            d = m.get("supported_durations")
            if d and len(d) > 4:
                d = f"{min(x for x in d if x > 0)}-{max(d)}s" + (" or auto" if -1 in d else "")
            print(f"   durations: {d}  resolutions: {m.get('supported_resolutions')}  ratios: {m.get('supported_aspect_ratios')}")
            print(f"   frames: {m.get('supported_frame_images')}  audio: {m.get('generate_audio')}  seed: {m.get('seed')}")
            if m.get("allowed_passthrough_parameters"):
                print(f"   extra options: {m['allowed_passthrough_parameters']}")
            print(f"   pricing: {m.get('pricing_skus')}")
            est, _ = estimate_video(m, 5, "720p" if "720p" in (m.get("supported_resolutions") or []) else (m.get("supported_resolutions") or [None])[0], False, False)
            if est is not None:
                print(f"   about {money(est)} for 5s silent at default resolution")
        else:
            params = m.get("supported_parameters") or {}
            if params:
                print(f"   options: {', '.join(params)}")
            if a.long:
                ep = call("GET", f"/images/models/{m['id']}/endpoints", auth=False)
                for e in ep.get("endpoints", ep.get("data", {}).get("endpoints", [])):
                    print(f"   {e.get('provider_name')}: {e.get('pricing')}  params: {json.dumps(e.get('supported_parameters'))}")
        print()
    print(f"{len(data)} {kind} model(s).")


def cmd_quote(a):
    m = find_model("video", a.model)
    usd, used = estimate_video(m, a.duration, a.resolution, a.audio, a.image_input)
    print(f"{a.model}, {a.duration}s, {a.resolution or 'default'}, {'with' if a.audio else 'no'} audio: about {money(usd)}")
    print(f"(price used: {used}; all prices: {m.get('pricing_skus')})")


def _check_video_args(m: dict, a) -> None:
    problems = []
    if a.duration is not None and m.get("supported_durations") and a.duration not in m["supported_durations"]:
        problems.append(f"duration {a.duration} not in {m['supported_durations']}")
    if a.resolution and m.get("supported_resolutions") and a.resolution not in m["supported_resolutions"]:
        problems.append(f"resolution {a.resolution} not in {m['supported_resolutions']}")
    if a.aspect and m.get("supported_aspect_ratios") and a.aspect not in m["supported_aspect_ratios"]:
        problems.append(f"aspect ratio {a.aspect} not in {m['supported_aspect_ratios']}")
    frames = m.get("supported_frame_images") or []
    if a.first_frame and "first_frame" not in frames:
        problems.append("this model does not take a first frame")
    if a.last_frame and "last_frame" not in frames:
        problems.append("this model does not take a last frame")
    if problems:
        sys.exit(f"{m['id']} cannot do that: " + "; ".join(problems))


def _parse_options(pairs: list[str]) -> dict:
    """--option slug.key=value  ->  {"slug": {"key": value}}; values parsed as JSON when possible."""
    out: dict = {}
    for p in pairs or []:
        if "=" not in p or "." not in p.split("=", 1)[0]:
            sys.exit(f"--option must look like provider.key=value, got {p}")
        k, v = p.split("=", 1)
        slug_, key = k.split(".", 1)
        try:
            val = json.loads(v)
        except json.JSONDecodeError:
            val = v
        node = out.setdefault(slug_, {})
        if slug_ == "google-vertex":  # Veo takes its keys inside "parameters"
            node = node.setdefault("parameters", {})
        node[key] = val
    return out


def cmd_video(a):
    m = find_model("video", a.model)
    _check_video_args(m, a)
    body: dict = {"model": a.model}
    if a.prompt:
        body["prompt"] = a.prompt
    for field, val in (("duration", a.duration), ("resolution", a.resolution), ("aspect_ratio", a.aspect),
                       ("size", a.size), ("seed", a.seed), ("previous_job_id", a.extend)):
        if val is not None:
            body[field] = val
    if a.audio is not None:
        body["generate_audio"] = a.audio
    frames = []
    for src, kind in ((a.first_frame, "first_frame"), (a.last_frame, "last_frame")):
        if src:
            frames.append({"type": "image_url", "image_url": {"url": media_ref(src)}, "frame_type": kind})
    if frames:
        body["frame_images"] = frames
    refs = [{"type": "image_url", "image_url": {"url": media_ref(s)}} for s in a.ref or []]
    refs += [{"type": "video_url", "video_url": {"url": media_ref(s)}} for s in a.ref_video or []]
    refs += [{"type": "audio_url", "audio_url": {"url": media_ref(s)}} for s in a.ref_audio or []]
    if refs:
        body["input_references"] = refs
    if a.option:
        body["provider"] = {"options": _parse_options(a.option)}

    usd, _ = estimate_video(m, a.duration or 5, a.resolution, bool(a.audio), bool(frames or a.ref))
    print(f"Estimated cost: about {money(usd)}")
    if a.dry_run:
        shown = json.loads(json.dumps(body))
        for group in ("frame_images", "input_references"):
            for item in shown.get(group, []):
                for v in item.values():
                    if isinstance(v, dict) and str(v.get("url", "")).startswith("data:"):
                        v["url"] = v["url"][:40] + "...(local file)"
        print(json.dumps(shown, indent=2))
        print("Dry run: nothing was sent.")
        return

    job = call("POST", "/videos", body)
    print(f"Submitted job {job['id']} (status: {job.get('status')})", flush=True)
    log(a.out_dir, {"type": "video_submitted", "job": job["id"], "model": a.model, "prompt": a.prompt,
                    "duration": a.duration, "resolution": a.resolution, "aspect": a.aspect, "estimate": usd})
    if a.no_wait:
        print(f"Not waiting. Later run: studio.py wait {job['id']}")
        return
    _wait(job, a.out_dir, a.prompt or a.model, a.name, a.timeout)


def _wait(job: dict, out_dir: Path, prompt: str, name: str | None, timeout: int) -> None:
    poll = job.get("polling_url") or f"{API}/videos/{job['id']}"
    if poll.startswith("/"):
        poll = "https://openrouter.ai" + poll
    start = time.time()
    status = job.get("status")
    while status not in ("completed", "failed", "cancelled", "expired"):
        if time.time() - start > timeout:
            print(f"Still {status} after {timeout}s. Resume with: studio.py wait {job['id']}")
            return
        time.sleep(10)
        job = call("GET", poll)
        if job.get("status") != status:
            status = job.get("status")
            print(f"  {int(time.time() - start)}s: {status}", flush=True)
    if status != "completed":
        log(out_dir, {"type": "video_failed", "job": job["id"], "status": status, "error": job.get("error")})
        sys.exit(f"Video {status}: {job.get('error') or 'no reason given'} (failed jobs are normally not charged)")

    urls = job.get("unsigned_urls") or [f"{API}/videos/{job['id']}/content?index=0"]
    saved = []
    for i, url in enumerate(urls):
        data = call("GET", url if url.startswith("http") else f"https://openrouter.ai{url}", raw=True,
                    auth=url.startswith("https://openrouter.ai/api/") or url.startswith("/api/"))
        p = out_path(out_dir, prompt, ".mp4", name, i if len(urls) > 1 else None)
        p.write_bytes(data)
        saved.append(str(p))
    cost = (job.get("usage") or {}).get("cost")
    log(out_dir, {"type": "video", "job": job["id"], "files": saved, "cost": cost, "prompt": prompt})
    for s in saved:
        print(f"Saved {s}")
    print(f"Actual cost: {money(cost)}")


def cmd_wait(a):
    job = call("GET", f"/videos/{a.job_id}")
    _wait(job, a.out_dir, a.name or a.job_id, a.name, a.timeout)


def cmd_image(a):
    body: dict = {"model": a.model, "prompt": a.prompt}
    for field, val in (("aspect_ratio", a.aspect), ("resolution", a.resolution), ("size", a.size),
                       ("n", a.n), ("seed", a.seed), ("quality", a.quality), ("output_format", a.format)):
        if val is not None:
            body[field] = val
    if a.ref:
        body["input_references"] = [{"type": "image_url", "image_url": {"url": media_ref(s)}} for s in a.ref]
    if a.dry_run:
        print(json.dumps({k: (f"{len(v)} reference image(s)" if k == "input_references" else v) for k, v in body.items()}, indent=2))
        print("Dry run: nothing was sent.")
        return
    res = call("POST", "/images", body)
    saved = []
    for i, item in enumerate(res.get("data", [])):
        mime = item.get("media_type") or "image/png"
        ext = mimetypes.guess_extension(mime) or ".png"
        ext = {".jpe": ".jpg", ".svgz": ".svg"}.get(ext, ext)
        p = out_path(a.out_dir, a.prompt, ext, a.name, i if len(res["data"]) > 1 else None)
        if item.get("b64_json"):
            p.write_bytes(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            p.write_bytes(call("GET", item["url"], auth=item["url"].startswith("https://openrouter.ai/api/"), raw=True))
        else:
            continue
        saved.append(str(p))
    if not saved:
        sys.exit(f"No image came back. Response: {json.dumps(res)[:1500]}")
    cost = (res.get("usage") or {}).get("cost")
    log(a.out_dir, {"type": "image", "model": a.model, "prompt": a.prompt, "files": saved, "cost": cost})
    for s in saved:
        print(f"Saved {s}")
    print(f"Actual cost: {money(cost)}")


def cmd_history(a):
    f = a.out_dir / "history.jsonl"
    if not f.exists():
        print("Nothing made yet.")
        return
    lines = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    done = [x for x in lines if x["type"] in ("video", "image")]
    for x in done[-a.last:]:
        print(f"{x['at']}  {x['type']:5}  {money(x.get('cost')):>8}  {x.get('model', '')}  {', '.join(x.get('files', []))}")
        print(f"   {x.get('prompt', '')[:160]}")
    total = sum(float(x.get("cost") or 0) for x in done)
    print(f"{len(done)} item(s), ${total:.2f} in total.")


# ------------------------------------------------------------------------------ main

def main():
    p = argparse.ArgumentParser(description="Make videos and images through OpenRouter.")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="where files and history go (default ./outputs)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("credits", help="show the account balance").set_defaults(fn=cmd_credits)

    s = sub.add_parser("models", help="list live models")
    s.add_argument("kind", choices=["video", "image"])
    s.add_argument("--search")
    s.add_argument("--long", action="store_true", help="full descriptions (and per-provider prices for images)")
    s.set_defaults(fn=cmd_models)

    s = sub.add_parser("quote", help="estimate a video's cost")
    s.add_argument("--model", required=True)
    s.add_argument("--duration", type=int, default=5)
    s.add_argument("--resolution")
    s.add_argument("--audio", action="store_true")
    s.add_argument("--image-input", action="store_true", help="the video starts from a picture")
    s.set_defaults(fn=cmd_quote)

    s = sub.add_parser("video", help="make a video")
    s.add_argument("--model", required=True)
    s.add_argument("--prompt")
    s.add_argument("--duration", type=int)
    s.add_argument("--resolution")
    s.add_argument("--aspect", help="e.g. 16:9, 9:16, 1:1")
    s.add_argument("--size", help="exact WIDTHxHEIGHT instead of resolution+aspect")
    s.add_argument("--audio", dest="audio", action="store_true", default=None, help="ask for sound")
    s.add_argument("--no-audio", dest="audio", action="store_false", help="ask for a silent video")
    s.add_argument("--first-frame", help="image file or URL the video starts on")
    s.add_argument("--last-frame", help="image file or URL the video ends on")
    s.add_argument("--ref", action="append", help="reference image (repeatable)")
    s.add_argument("--ref-video", action="append", help="reference/source video URL or file (repeatable)")
    s.add_argument("--ref-audio", action="append", help="reference audio URL or file (repeatable)")
    s.add_argument("--extend", metavar="JOB_ID", help="edit or continue a finished job (only some models)")
    s.add_argument("--seed", type=int)
    s.add_argument("--option", action="append", help="provider option as slug.key=value (repeatable)")
    s.add_argument("--name", help="file name without extension")
    s.add_argument("--timeout", type=int, default=540, help="seconds to wait before handing back (default 540)")
    s.add_argument("--no-wait", action="store_true")
    s.add_argument("--dry-run", action="store_true", help="show the request and estimate, send nothing")
    s.set_defaults(fn=cmd_video)

    s = sub.add_parser("wait", help="wait for a video job and download it")
    s.add_argument("job_id")
    s.add_argument("--name")
    s.add_argument("--timeout", type=int, default=540)
    s.set_defaults(fn=cmd_wait)

    s = sub.add_parser("image", help="make images")
    s.add_argument("--model", required=True)
    s.add_argument("--prompt", required=True)
    s.add_argument("--aspect")
    s.add_argument("--resolution", help="e.g. 1K, 2K, 4K (model dependent)")
    s.add_argument("--size")
    s.add_argument("--n", type=int)
    s.add_argument("--seed", type=int)
    s.add_argument("--quality", help="OpenAI models: low, medium, high")
    s.add_argument("--format", help="png, jpeg, webp (model dependent)")
    s.add_argument("--ref", action="append", help="reference/edit image file or URL (repeatable)")
    s.add_argument("--name")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_image)

    s = sub.add_parser("history", help="what was made and what it cost")
    s.add_argument("--last", type=int, default=10)
    s.set_defaults(fn=cmd_history)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
