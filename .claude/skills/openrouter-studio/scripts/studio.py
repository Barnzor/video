#!/usr/bin/env python3
"""
OpenRouter studio: make videos and images through OpenRouter, only from an approved plan.

Standard library only. Reads the key from OPENROUTER_API_KEY.

Free:
  studio.py credits                                   account balance
  studio.py models video|image [--search T] [--long]  live model list with options and prices
  studio.py quote --model M --duration 5 --resolution 720p [--audio] [--image-input]
  studio.py plan template                             print an empty plan to start from
  studio.py plan show PLAN.json [--items a,b]         the whole plan in plain words, with costs
  studio.py plan approve PLAN.json --items a,b        record the user's yes for these items as they stand
  studio.py plan pick PLAN.json ITEM TAKE             choose which take later items build on
  studio.py plan verdict PLAN.json ITEM TAKE keep|reject --reason "..."   log the judgement
  studio.py history [--last 10]

Costs money (refuses anything not approved exactly as it stands now):
  studio.py plan run PLAN.json --items a,b --max-usd 2.50
  studio.py plan wait PLAN.json                       collect videos that were still rendering
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
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

VIDEO_SETTINGS = ("duration", "resolution", "aspect", "size", "seed", "audio")
IMAGE_SETTINGS = ("aspect", "resolution", "size", "n", "seed", "quality", "format")


class StudioError(Exception):
    pass


# ----------------------------------------------------------------------------- http

def _key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise StudioError("OPENROUTER_API_KEY is not set. Save it in the environment settings, then try again.")
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
            raise StudioError(
                "BLOCKED BY ACCOUNT PRIVACY SETTING: the OpenRouter account only allows Zero Data Retention "
                "providers, and no provider for this model offers that (no video model does). Nothing was charged. "
                "Change it at https://openrouter.ai/settings/privacy, in the workspace this key belongs to.")
        if e.code == 402:
            raise StudioError("Not enough OpenRouter credit for this. Top up at https://openrouter.ai/settings/credits")
        raise StudioError(f"OpenRouter said {e.code} for {method} {path}:\n{detail}")
    except urllib.error.URLError as e:
        raise StudioError(f"Could not reach OpenRouter: {e.reason}")
    return payload if raw else json.loads(payload)


# ---------------------------------------------------------------------------- utils

def media_ref(src: str) -> str:
    """A URL is passed through; a local file becomes a base64 data URL."""
    if re.match(r"^(https?:|data:)", src):
        return src
    p = Path(src).expanduser()
    if not p.is_file():
        raise StudioError(f"No such file: {src}")
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def keep_out_of_git(out_dir: Path) -> None:
    """If out_dir is inside a git repo, list it in that repo's local .git/info/exclude (never committed)."""
    here = out_dir.resolve().parent
    for d in (here, *here.parents):
        git = d / ".git"
        if git.is_dir():
            try:
                rel = out_dir.resolve().relative_to(d).as_posix()
                exclude = git / "info" / "exclude"
                lines = exclude.read_text().splitlines() if exclude.exists() else []
                if f"/{rel}/" not in lines:
                    exclude.parent.mkdir(parents=True, exist_ok=True)
                    with open(exclude, "a") as f:
                        f.write(f"\n# media from openrouter-studio\n/{rel}/\n")
            except (OSError, ValueError):
                pass
            return


def log(out_dir: Path, entry: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    keep_out_of_git(out_dir)
    entry = {"at": dt.datetime.now().isoformat(timespec="seconds"), **entry}
    with open(out_dir / "history.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


def money(x) -> str:
    return "unknown" if x is None else f"${float(x):.2f}" if float(x) >= 0.1 else f"${float(x):.3f}"


_cache: dict = {}


def model_list(kind: str) -> list[dict]:
    if kind not in _cache:
        _cache[kind] = call("GET", f"/{'videos' if kind == 'video' else 'images'}/models", auth=False)["data"]
    return _cache[kind]


def find_model(kind: str, model_id: str) -> dict:
    for m in model_list(kind):
        if m["id"] == model_id:
            return m
    stem = model_id.split("/")[-1].split("-")[0]
    close = [m["id"] for m in model_list(kind) if stem in m["id"]][:8]
    raise StudioError(f"No {kind} model called {model_id}." + (f" Close matches: {', '.join(close)}" if close else ""))


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
        mode = "image_to_video" if image_input else "text_to_video"
        if k.startswith(mode):
            s += 3
        elif k.startswith(("image_to_video", "text_to_video")):
            s -= 10
        for bad in ("long_", "reference", "continuation", "with_video_input", "minimum", "image_input", "megapixel"):
            if bad in k:
                s -= 20
        return s

    def pick(cands: list[str]) -> str | None:
        cands = sorted(cands, key=score, reverse=True)
        return cands[0] if cands and score(cands[0]) > -10 else None

    extra = skus.get("cents_per_image_input", 0) / 100 if image_input else 0.0
    per_sec = [k for k in skus if "duration_seconds" in k]
    cents = [k for k in skus if k.startswith("cents_per") and "second" in k and "megapixel" not in k]
    tokens = [k for k in skus if k.startswith("video_tokens")]
    usd, used = None, ""
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


def estimate_image(model_id: str, settings: dict, n_refs: int) -> tuple[float | None, float | None]:
    """Rough (low, high) USD for one image request. Token prices use typical image token counts."""
    try:
        ep = call("GET", f"/images/models/{model_id}/endpoints", auth=False)
    except StudioError:
        return None, None
    ep = ep.get("data", ep)
    endpoints = ep.get("endpoints") or []
    if not endpoints:
        return None, None
    res = str(settings.get("resolution") or "1K").upper()
    mp = {"512": 0.25, "768": 0.6, "1K": 1, "1.5K": 2.25, "2K": 4, "4K": 16}.get(res, 1)
    q = settings.get("quality") or "medium"
    out_tokens = {"low": 272, "medium": 1056, "high": 4160, "auto": 1056}.get(q, 1056) if model_id.startswith("openai/") \
        else (2000 if res == "4K" else 1120)
    lo = hi = 0.0
    for p in endpoints[0].get("pricing") or []:
        cost, unit, what = float(p["cost_usd"]), p["unit"], p["billable"]
        if what == "output_image":
            if unit == "image":
                lo = cost if lo == 0 else min(lo, cost)
                hi = max(hi, cost)
            elif unit == "megapixel":
                lo = hi = cost * mp
            elif unit == "token":
                lo = hi = cost * out_tokens
            elif unit == "request":
                lo, hi = lo + cost, hi + cost
        elif what == "input_image" and n_refs:
            per = cost * (1000 if unit == "token" else 1)
            lo, hi = lo + per * n_refs, hi + per * n_refs
    n = int(settings.get("n") or 1)
    return (round(lo * n, 4), round(hi * n, 4)) if hi else (None, None)


# ------------------------------------------------------------------ request building

def video_body(spec: dict) -> dict:
    s, inp = spec.get("settings", {}), spec.get("inputs", {})
    m = find_model("video", spec["model"])
    problems = []
    if s.get("duration") is not None and m.get("supported_durations") and s["duration"] not in m["supported_durations"]:
        problems.append(f"duration {s['duration']} not in {m['supported_durations']}")
    if s.get("resolution") and m.get("supported_resolutions") and s["resolution"] not in m["supported_resolutions"]:
        problems.append(f"resolution {s['resolution']} not in {m['supported_resolutions']}")
    if s.get("aspect") and m.get("supported_aspect_ratios") and s["aspect"] not in m["supported_aspect_ratios"]:
        problems.append(f"aspect ratio {s['aspect']} not in {m['supported_aspect_ratios']}")
    frames_ok = m.get("supported_frame_images") or []
    for kind in ("first_frame", "last_frame"):
        if inp.get(kind) and kind not in frames_ok:
            problems.append(f"this model does not take a {kind.replace('_', ' ')}")
    if problems:
        raise StudioError(f"{m['id']} cannot do that: " + "; ".join(problems))

    body: dict = {"model": spec["model"]}
    if spec.get("prompt"):
        body["prompt"] = spec["prompt"]
    for field, key in (("duration", "duration"), ("resolution", "resolution"), ("aspect_ratio", "aspect"),
                       ("size", "size"), ("seed", "seed")):
        if s.get(key) is not None:
            body[field] = s[key]
    if s.get("audio") is not None:
        body["generate_audio"] = bool(s["audio"])
    if inp.get("extend"):
        body["previous_job_id"] = inp["extend"]
    frames = [{"type": "image_url", "image_url": {"url": media_ref(inp[k])}, "frame_type": k}
              for k in ("first_frame", "last_frame") if inp.get(k)]
    if frames:
        body["frame_images"] = frames
    refs = [{"type": "image_url", "image_url": {"url": media_ref(x)}} for x in inp.get("refs") or []]
    refs += [{"type": "video_url", "video_url": {"url": media_ref(x)}} for x in inp.get("ref_videos") or []]
    refs += [{"type": "audio_url", "audio_url": {"url": media_ref(x)}} for x in inp.get("ref_audios") or []]
    if refs:
        body["input_references"] = refs
    if spec.get("options"):
        body["provider"] = {"options": provider_options(spec["options"])}
    return body


def image_body(spec: dict) -> dict:
    s, inp = spec.get("settings", {}), spec.get("inputs", {})
    body: dict = {"model": spec["model"], "prompt": spec["prompt"]}
    for field, key in (("aspect_ratio", "aspect"), ("resolution", "resolution"), ("size", "size"), ("n", "n"),
                       ("seed", "seed"), ("quality", "quality"), ("output_format", "format")):
        if s.get(key) is not None:
            body[field] = s[key]
    if inp.get("refs"):
        body["input_references"] = [{"type": "image_url", "image_url": {"url": media_ref(x)}} for x in inp["refs"]]
    if spec.get("options"):
        body["provider"] = {"options": provider_options(spec["options"])}
    return body


def provider_options(opts: dict) -> dict:
    """{"slug.key": value} -> {"slug": {"key": value}}; Veo (google-vertex) keys go inside "parameters"."""
    out: dict = {}
    for k, v in opts.items():
        if "." not in k:
            raise StudioError(f"Option names look like provider.key, got {k}")
        slug_, key = k.split(".", 1)
        node = out.setdefault(slug_, {})
        if slug_ == "google-vertex":
            node = node.setdefault("parameters", {})
        node[key] = v
    return out


# ----------------------------------------------------------------------- generation

def save_images(res: dict, out_dir: Path, base: str) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    keep_out_of_git(out_dir)
    saved = []
    items = res.get("data", [])
    for i, item in enumerate(items):
        mime = item.get("media_type") or "image/png"
        ext = {".jpe": ".jpg", ".svgz": ".svg"}.get(mimetypes.guess_extension(mime) or ".png", mimetypes.guess_extension(mime) or ".png")
        p = out_dir / f"{base}{f'-{i + 1}' if len(items) > 1 else ''}{ext}"
        if item.get("b64_json"):
            p.write_bytes(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            p.write_bytes(call("GET", item["url"], auth=item["url"].startswith("https://openrouter.ai/api/"), raw=True))
        else:
            continue
        saved.append(str(p))
    if not saved:
        raise StudioError(f"No image came back. Response: {json.dumps(res)[:1500]}")
    return saved


def poll_video(job_id: str) -> dict:
    return call("GET", f"/videos/{job_id}")


def download_video(job: dict, out_dir: Path, base: str) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    keep_out_of_git(out_dir)
    urls = job.get("unsigned_urls") or [f"{API}/videos/{job['id']}/content?index=0"]
    saved = []
    for i, url in enumerate(urls):
        full = url if url.startswith("http") else f"https://openrouter.ai{url}"
        data = call("GET", full, raw=True, auth=full.startswith("https://openrouter.ai/api/"))
        p = out_dir / f"{base}{f'-{i + 1}' if len(urls) > 1 else ''}.mp4"
        p.write_bytes(data)
        saved.append(str(p))
    return saved


# ----------------------------------------------------------------------------- plans

PLAN_TEMPLATE = {
    "title": "Short name for this piece",
    "brief": "Goal, where it will be posted, audience, look and feel, length, budget.",
    "script": "Every word that will be spoken, sung or shown on screen, exactly. Empty if none.",
    "items": [
        {
            "id": "frame1",
            "type": "image",
            "purpose": "First frame of shot 1",
            "model": "google/gemini-3.1-flash-image",
            "prompt": "The exact prompt text that will be sent.",
            "settings": {"aspect": "9:16", "resolution": "2K"},
            "inputs": {"refs": []},
            "options": {},
        },
        {
            "id": "shot1",
            "type": "video",
            "purpose": "Shot 1: the hook",
            "model": "kwaivgi/kling-v3.0-pro",
            "prompt": "Motion and camera only, because it starts from frame1.",
            "settings": {"duration": 5, "resolution": "720p", "aspect": "9:16", "audio": False},
            "inputs": {"first_frame": "@frame1"},
            "options": {},
        },
    ],
}

SPEC_KEYS = ("type", "model", "prompt", "settings", "inputs", "options")

# Known prompt-length limits in characters (from vendor or reseller docs; Nov 2026). Prefix match on model id.
PROMPT_CAPS = {
    "runway/": 1000, "kwaivgi/kling": 2500, "minimax/hailuo-2": 2000, "minimax/hailuo-3": 7000,
    "alibaba/wan-2.6": 1500, "alibaba/wan-2.7": 5000, "black-forest-labs/flux-video-edit": 4096,
}


def prompt_cap(model_id: str) -> int | None:
    for prefix, cap in PROMPT_CAPS.items():
        if model_id.startswith(prefix):
            return cap
    return None


def load_plan(path: Path) -> dict:
    try:
        plan = json.loads(path.read_text())
    except FileNotFoundError:
        raise StudioError(f"No plan at {path}")
    except json.JSONDecodeError as e:
        raise StudioError(f"The plan is not valid JSON: {e}")
    ids = [it.get("id") for it in plan.get("items", [])]
    if len(ids) != len(set(ids)) or not all(ids):
        raise StudioError("Every item needs a unique id.")
    for it in plan["items"]:
        if it.get("type") not in ("image", "video"):
            raise StudioError(f"Item {it['id']}: type must be image or video.")
        if not it.get("model"):
            raise StudioError(f"Item {it['id']}: no model.")
        it.setdefault("settings", {})
        it.setdefault("inputs", {})
        it.setdefault("options", {})
        it.setdefault("takes", [])
        allowed = VIDEO_SETTINGS if it["type"] == "video" else IMAGE_SETTINGS
        unknown = set(it["settings"]) - set(allowed)
        if unknown:
            raise StudioError(f"Item {it['id']}: unknown settings {sorted(unknown)}; allowed: {list(allowed)}")
    return plan


def save_plan(path: Path, plan: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(plan, indent=2) + "\n")
    tmp.replace(path)


def spec_of(it: dict) -> dict:
    return {k: it.get(k) for k in SPEC_KEYS}


def fingerprint(it: dict) -> str:
    return hashlib.sha256(json.dumps(spec_of(it), sort_keys=True).encode()).hexdigest()[:16]


def chosen_take(it: dict) -> dict | None:
    done = [t for t in it.get("takes", []) if t.get("status") == "done"]
    if it.get("pick"):
        for t in done:
            if t["take"] == it["pick"]:
                return t
    usable = [t for t in done if t.get("verdict") != "reject"]
    return usable[-1] if usable else None


def resolve(value, items: dict, plan_dir: Path, need: bool):
    """'@id' -> the chosen take's file (or job id for 'extend'); paths relative to the plan's folder."""
    if isinstance(value, list):
        return [resolve(v, items, plan_dir, need) for v in value]
    if not isinstance(value, str):
        return value
    if value.startswith("@"):
        ref = items.get(value[1:])
        if not ref:
            raise StudioError(f"{value} does not match any item id.")
        t = chosen_take(ref)
        if not t:
            if need:
                raise StudioError(f"{value} has not been made yet (or no take was kept). Make it first.")
            return None
        return t
    if re.match(r"^(https?:|data:)", value):
        return value
    p = Path(value)
    return str(p if p.is_absolute() else (plan_dir / p))


def resolved_inputs(it: dict, items: dict, plan_dir: Path, need: bool) -> dict:
    out = {}
    for k, v in (it.get("inputs") or {}).items():
        r = resolve(v, items, plan_dir, need)
        if k == "extend":
            out[k] = r.get("job") if isinstance(r, dict) else r
        elif isinstance(r, list):
            out[k] = [x["files"][0] if isinstance(x, dict) else x for x in r if x is not None]
        else:
            out[k] = r["files"][0] if isinstance(r, dict) else r
    return out


def describe_inputs(it: dict, items: dict, plan_dir: Path) -> list[str]:
    lines = []
    for k, v in (it.get("inputs") or {}).items():
        vals = v if isinstance(v, list) else [v]
        for one in vals:
            if not one:
                continue
            if isinstance(one, str) and one.startswith("@"):
                ref = items.get(one[1:])
                t = chosen_take(ref) if ref else None
                made = ref and any(x.get("status") == "done" for x in ref.get("takes", []))
                where = (f"take {t['take']}: {t['files'][0] if k != 'extend' else t.get('job')}" if t
                         else "NO KEPT TAKE: all takes rejected" if made else "NOT MADE YET")
                lines.append(f"{k.replace('_', ' ')}: {one} ({where})")
            else:
                lines.append(f"{k.replace('_', ' ')}: {one}")
    return lines


def estimate_item(it: dict) -> tuple[float | None, float | None]:
    s = it["settings"]
    if it["type"] == "video":
        m = find_model("video", it["model"])
        inp = it.get("inputs") or {}
        usd, _ = estimate_video(m, int(s.get("duration") or 5), s.get("resolution"), bool(s.get("audio")),
                                bool(inp.get("first_frame") or inp.get("last_frame") or inp.get("refs")))
        return usd, usd
    return estimate_image(it["model"], s, len((it.get("inputs") or {}).get("refs") or []))


def fmt_range(lo, hi) -> str:
    if lo is None:
        return "unknown (check the model's prices)"
    return money(lo) if abs((hi or lo) - lo) < 0.0005 else f"{money(lo)} to {money(hi)}"


def changed_since_last_take(it: dict) -> list[str]:
    if not it["takes"]:
        return []
    last = it["takes"][-1].get("spec") or {}
    return [k for k in SPEC_KEYS if json.dumps(last.get(k), sort_keys=True) != json.dumps(it.get(k), sort_keys=True)]


def cmd_plan_template(_):
    print(json.dumps(PLAN_TEMPLATE, indent=2))


def cmd_plan_show(a):
    plan = load_plan(a.plan)
    items = {it["id"]: it for it in plan["items"]}
    wanted = a.items.split(",") if a.items else list(items)
    plan_dir = a.plan.parent
    print(f"# {plan.get('title', 'Untitled plan')}\n")
    if plan.get("brief"):
        print(f"Brief: {plan['brief']}\n")
    print("Script (every spoken or on-screen word):")
    print(f"  {plan.get('script') or '(none)'}\n")
    total_lo = total_hi = 0.0
    unknown = False
    for iid in wanted:
        it = items.get(iid)
        if not it:
            raise StudioError(f"No item called {iid}.")
        lo, hi = estimate_item(it)
        approved = it.get("approved") == fingerprint(it)
        state = "APPROVED" if approved else ("approval out of date: changed since the yes" if it.get("approved") else "not approved yet")
        print(f"## {iid}: {it.get('purpose', '')}   [{it['type']}, {state}]")
        print(f"  Model:    {it['model']}")
        nice = {True: "on", False: "off"}
        print(f"  Settings: {', '.join(f'{k} {nice.get(v, v) if isinstance(v, bool) else v}' for k, v in it['settings'].items()) or 'model defaults'}")
        for line in describe_inputs(it, items, plan_dir):
            print(f"  Input:    {line}")
        if it.get("options"):
            print(f"  Options:  {it['options']}")
        prompt = it.get("prompt") or ""
        words = len(prompt.split())
        cap = prompt_cap(it["model"])
        print(f"  Prompt:   {prompt or '(none)'}")
        print(f"            ({words} words, {len(prompt)} characters" + (f"; limit about {cap}" if cap else "") + ")")
        if cap and len(prompt) > cap:
            print("            TOO LONG for this model: shorten before approval.")
        print(f"  Cost:     {fmt_range(lo, hi)}")
        if it["takes"]:
            done = [t for t in it["takes"] if t.get("status") == "done"]
            pick = chosen_take(it)
            print(f"  Takes:    {len(done)} made" + (f", using take {pick['take']} ({pick['files'][0]})" if pick else ""))
            for t in it["takes"]:
                if t.get("verdict"):
                    print(f"            take {t['take']}: {t['verdict']}" + (f": {t['reason']}" if t.get("reason") else ""))
            running = [t for t in it["takes"] if t.get("status") == "running"]
            if running:
                print(f"            {len(running)} still rendering: run 'plan wait'")
            ch = changed_since_last_take(it)
            if ch:
                print(f"  Changed since last take: {', '.join(ch)}")
        print()
        if lo is None:
            unknown = True
        else:
            total_lo += lo
            total_hi += hi or lo
    print(f"Total for these {len(wanted)} item(s): {fmt_range(total_lo, total_hi)}" + (" plus items with unknown price" if unknown else ""))
    print("Final prices come from OpenRouter after each item is made; estimates for images are approximate.")


def cmd_plan_approve(a):
    plan = load_plan(a.plan)
    items = {it["id"]: it for it in plan["items"]}
    for iid in a.items.split(","):
        if iid not in items:
            raise StudioError(f"No item called {iid}.")
        items[iid]["approved"] = fingerprint(items[iid])
        print(f"Approved {iid} exactly as it stands now.")
    save_plan(a.plan, plan)


def cmd_plan_verdict(a):
    plan = load_plan(a.plan)
    it = next((x for x in plan["items"] if x["id"] == a.item), None)
    take = next((t for t in (it or {}).get("takes", []) if t["take"] == a.take), None)
    if not take:
        raise StudioError(f"{a.item} has no take {a.take}.")
    take["verdict"] = a.verdict
    take["reason"] = a.reason or ""
    if a.verdict == "keep" and take.get("status") == "done":
        it["pick"] = a.take
    elif a.verdict == "reject" and it.get("pick") == a.take:
        it["pick"] = None
    save_plan(a.plan, plan)
    print(f"{a.item} take {a.take}: {a.verdict}" + (f" ({a.reason})" if a.reason else ""))


def cmd_plan_pick(a):
    plan = load_plan(a.plan)
    it = next((x for x in plan["items"] if x["id"] == a.item), None)
    if not it or not any(t["take"] == a.take and t.get("status") == "done" for t in it["takes"]):
        raise StudioError(f"{a.item} has no finished take {a.take}.")
    it["pick"] = a.take
    save_plan(a.plan, plan)
    print(f"{a.item}: later items will use take {a.take}.")


def _finish_take(it: dict, take: dict, job: dict, plan_dir: Path, out_dir: Path) -> None:
    status = job.get("status")
    if status == "completed":
        take["files"] = download_video(job, out_dir, f"{it['id']}-take{take['take']}")
        take["cost"] = (job.get("usage") or {}).get("cost")
        take["status"] = "done"
        log(out_dir, {"type": "video", "plan_item": it["id"], "take": take["take"], "model": it["model"],
                      "prompt": it.get("prompt"), "files": take["files"], "cost": take["cost"], "job": job["id"]})
        print(f"{it['id']} take {take['take']}: saved {', '.join(take['files'])} (cost {money(take['cost'])})", flush=True)
    elif status in ("failed", "cancelled", "expired"):
        take["status"] = "failed"
        take["error"] = job.get("error") or status
        print(f"{it['id']} take {take['take']}: {status}: {take['error']} (failed jobs are normally not charged)", flush=True)


def precheck(it: dict, items: dict, plan_dir: Path, earlier: set[str]) -> None:
    """Fail before any spending if a setting, model or input is wrong."""
    s = it["settings"]
    if it["type"] == "video":
        m = find_model("video", it["model"])
        checks = (("duration", "supported_durations"), ("resolution", "supported_resolutions"), ("aspect", "supported_aspect_ratios"))
        for key, field in checks:
            if s.get(key) is not None and m.get(field) and s[key] not in m[field]:
                raise StudioError(f"{it['id']}: {it['model']} cannot do {key} {s[key]} (it offers {m[field]}). Nothing was sent.")
        for kind in ("first_frame", "last_frame"):
            if (it.get("inputs") or {}).get(kind) and kind not in (m.get("supported_frame_images") or []):
                raise StudioError(f"{it['id']}: {it['model']} does not take a {kind.replace('_', ' ')}. Nothing was sent.")
    else:
        find_model("image", it["model"])
    if not it.get("prompt") and it["type"] == "image":
        raise StudioError(f"{it['id']}: images need a prompt.")
    cap = prompt_cap(it["model"])
    if cap and len(it.get("prompt") or "") > cap:
        raise StudioError(f"{it['id']}: prompt is {len(it['prompt'])} characters; {it['model']} allows about {cap}. Nothing was sent.")
    for v in (it.get("inputs") or {}).values():
        for one in v if isinstance(v, list) else [v]:
            if not isinstance(one, str) or not one:
                continue
            if one.startswith("@"):
                ref = items.get(one[1:])
                if not ref:
                    raise StudioError(f"{it['id']}: {one} does not match any item. Nothing was sent.")
                if not chosen_take(ref) and one[1:] not in earlier:
                    raise StudioError(f"{it['id']}: {one} has not been made yet; include it earlier in --items. Nothing was sent.")
            elif not re.match(r"^(https?:|data:)", one):
                p = Path(one) if Path(one).is_absolute() else plan_dir / one
                if not p.is_file():
                    raise StudioError(f"{it['id']}: input file {one} not found. Nothing was sent.")


def cmd_plan_run(a):
    plan = load_plan(a.plan)
    plan_dir = a.plan.parent
    out_dir = plan_dir
    items = {it["id"]: it for it in plan["items"]}
    wanted = a.items.split(",")
    for iid in wanted:
        if iid not in items:
            raise StudioError(f"No item called {iid}.")
        if items[iid].get("approved") != fingerprint(items[iid]):
            raise StudioError(f"{iid} is not approved as it stands now. Show the plan, get a yes, then run 'plan approve'.")
    # Check everything before spending anything.
    for n, iid in enumerate(wanted):
        precheck(items[iid], items, plan_dir, earlier=set(wanted[:n]))
    est = 0.0
    for iid in wanted:
        lo, hi = estimate_item(items[iid])
        est += hi or lo or 0
    if est > a.max_usd + 1e-9:
        raise StudioError(f"Estimated ${est:.2f} is over the agreed limit of ${a.max_usd:.2f}. Nothing was sent.")
    running: list[tuple[dict, dict]] = []
    for iid in wanted:
        it = items[iid]
        spec = spec_of(it)
        take = {"take": len(it["takes"]) + 1, "at": dt.datetime.now().isoformat(timespec="seconds"),
                "spec": spec_of(it), "status": "running"}
        try:
            spec["inputs"] = resolved_inputs(it, items, plan_dir, need=True)
            take["inputs_used"] = spec["inputs"]
            if it["type"] == "image":
                res = call("POST", "/images", image_body(spec))
                take["files"] = save_images(res, out_dir, f"{iid}-take{take['take']}")
                take["cost"] = (res.get("usage") or {}).get("cost")
                take["status"] = "done"
                log(out_dir, {"type": "image", "plan_item": iid, "take": take["take"], "model": it["model"],
                              "prompt": it.get("prompt"), "files": take["files"], "cost": take["cost"]})
                print(f"{iid} take {take['take']}: saved {', '.join(take['files'])} (cost {money(take['cost'])})", flush=True)
            else:
                job = call("POST", "/videos", video_body(spec))
                take["job"] = job["id"]
                running.append((it, take))
                print(f"{iid} take {take['take']}: rendering (job {job['id']})", flush=True)
        except StudioError as e:
            take["status"] = "failed"
            take["error"] = str(e)
            print(f"{iid}: FAILED: {e}", flush=True)
        it["takes"].append(take)
        save_plan(a.plan, plan)
    _wait_takes(a.plan, plan, running, a.timeout)


def _wait_takes(plan_path: Path, plan: dict, running: list[tuple[dict, dict]], timeout: int) -> None:
    start = time.time()
    while running:
        if time.time() - start > timeout:
            print(f"{len(running)} video(s) still rendering. Collect them later with: plan wait {plan_path}")
            break
        time.sleep(10)
        still = []
        for it, take in running:
            try:
                job = poll_video(take["job"])
            except StudioError as e:
                print(f"{it['id']}: could not check ({e}); will retry", flush=True)
                still.append((it, take))
                continue
            _finish_take(it, take, job, plan_path.parent, plan_path.parent)
            if take["status"] == "running":
                still.append((it, take))
            else:
                save_plan(plan_path, plan)
        running = still
    save_plan(plan_path, plan)
    spent = sum(float(t.get("cost") or 0) for it in plan["items"] for t in it["takes"])
    print(f"Spent on this plan so far: ${spent:.2f}")


def cmd_plan_wait(a):
    plan = load_plan(a.plan)
    running = [(it, t) for it in plan["items"] for t in it["takes"] if t.get("status") == "running"]
    if not running:
        print("Nothing is rendering.")
        return
    _wait_takes(a.plan, plan, running, a.timeout)


# ------------------------------------------------------------------ other commands

def cmd_credits(_):
    d = call("GET", "/credits")["data"]
    left = d["total_credits"] - d["total_usage"]
    print(f"Balance: ${left:.2f} left (bought ${d['total_credits']:.2f}, used ${d['total_usage']:.2f})")


def cmd_models(a):
    data = model_list(a.kind)
    if a.search:
        q = a.search.lower()
        data = [m for m in data if q in m["id"].lower() or q in (m.get("description") or "").lower()]
    for m in data:
        print(f"## {m['id']}  ({m.get('name', '')})")
        if a.long:
            print(f"   {(m.get('description') or '').strip()}")
        if a.kind == "video":
            d = m.get("supported_durations")
            if d and len(d) > 4:
                d = f"{min(x for x in d if x > 0)}-{max(d)}s" + (" or auto" if -1 in d else "")
            print(f"   durations: {d}  resolutions: {m.get('supported_resolutions')}  ratios: {m.get('supported_aspect_ratios')}")
            print(f"   frames: {m.get('supported_frame_images')}  audio: {m.get('generate_audio')}  seed: {m.get('seed')}")
            if m.get("allowed_passthrough_parameters"):
                print(f"   extra options: {m['allowed_passthrough_parameters']}")
            print(f"   pricing: {m.get('pricing_skus')}")
        else:
            params = m.get("supported_parameters") or {}
            if params:
                print(f"   options: {', '.join(params)}")
            if a.long:
                ep = call("GET", f"/images/models/{m['id']}/endpoints", auth=False)
                ep = ep.get("data", ep)
                for e in ep.get("endpoints", []):
                    print(f"   {e.get('provider_name')}: {e.get('pricing')}  params: {json.dumps(e.get('supported_parameters'))}")
        print()
    print(f"{len(data)} {a.kind} model(s).")


def cmd_quote(a):
    m = find_model("video", a.model)
    usd, used = estimate_video(m, a.duration, a.resolution, a.audio, a.image_input)
    print(f"{a.model}, {a.duration}s, {a.resolution or 'default'}, {'with' if a.audio else 'no'} audio: about {money(usd)}")
    print(f"(price used: {used}; all prices: {m.get('pricing_skus')})")


def cmd_history(a):
    files = sorted(Path(".").glob("**/history.jsonl")) if a.all else [a.out_dir / "history.jsonl"]
    rows = []
    for f in files:
        if f.exists():
            rows += [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    done = sorted([x for x in rows if x.get("type") in ("video", "image")], key=lambda x: x["at"])
    if not done:
        print("Nothing made yet.")
        return
    for x in done[-a.last:]:
        print(f"{x['at']}  {x['type']:5}  {money(x.get('cost')):>8}  {x.get('model', '')}  {', '.join(x.get('files', []))}")
        print(f"   {(x.get('prompt') or '')[:160]}")
    total = sum(float(x.get("cost") or 0) for x in done)
    print(f"{len(done)} item(s), ${total:.2f} in total.")


# ------------------------------------------------------------------------------ main

def main():
    p = argparse.ArgumentParser(description="Make videos and images through OpenRouter, from approved plans.")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="for history (default ./outputs)")
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

    s = sub.add_parser("history", help="what was made and what it cost")
    s.add_argument("--last", type=int, default=20)
    s.add_argument("--all", action="store_true", help="every history.jsonl under the current folder")
    s.set_defaults(fn=cmd_history)

    pl = sub.add_parser("plan", help="production plans").add_subparsers(dest="plan_cmd", required=True)
    s = pl.add_parser("template")
    s.set_defaults(fn=cmd_plan_template)
    s = pl.add_parser("show")
    s.add_argument("plan", type=Path)
    s.add_argument("--items")
    s.set_defaults(fn=cmd_plan_show)
    s = pl.add_parser("approve")
    s.add_argument("plan", type=Path)
    s.add_argument("--items", required=True)
    s.set_defaults(fn=cmd_plan_approve)
    s = pl.add_parser("verdict", help="record keep/reject and why, for learning")
    s.add_argument("plan", type=Path)
    s.add_argument("item")
    s.add_argument("take", type=int)
    s.add_argument("verdict", choices=["keep", "reject"])
    s.add_argument("--reason")
    s.set_defaults(fn=cmd_plan_verdict)
    s = pl.add_parser("pick")
    s.add_argument("plan", type=Path)
    s.add_argument("item")
    s.add_argument("take", type=int)
    s.set_defaults(fn=cmd_plan_pick)
    s = pl.add_parser("run")
    s.add_argument("plan", type=Path)
    s.add_argument("--items", required=True, help="comma-separated ids, in order")
    s.add_argument("--max-usd", type=float, required=True, help="refuse if the estimate is above this")
    s.add_argument("--timeout", type=int, default=540, help="seconds to wait for videos before handing back")
    s.set_defaults(fn=cmd_plan_run)
    s = pl.add_parser("wait")
    s.add_argument("plan", type=Path)
    s.add_argument("--timeout", type=int, default=540)
    s.set_defaults(fn=cmd_plan_wait)

    a = p.parse_args()
    try:
        a.fn(a)
    except StudioError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
