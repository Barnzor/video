# Which model for which job

Prices are from OpenRouter's live list in November 2026 and change. Check with `quote` (video) or
`models image --long` before quoting the user. The picks below come from each model's own
description and price, not from side-by-side testing. Treat them as starting points, and record
what the user actually prefers under **House preferences** at the bottom.

## House preferences

Update this section as you learn what this user likes, e.g. "Prefers Kling for people,
dislikes Veo's colour", "Always vertical for TikTok", "Budget: under $1 per clip unless told".
These override the defaults below. Commit the change so it sticks.

- (nothing recorded yet)

## Video

Rough cost for a 5-second, 720p, silent clip unless noted. Sound usually adds 25 to 100%.

| Job | First choice | Why | Cheaper draft | Premium |
|---|---|---|---|---|
| Realistic, cinematic shot with sound or dialogue | `google/veo-3.1-fast` (~$0.48 for 6 s with audio at 720p; 4, 6 or 8 s only) | Native synced sound and speech, strong realism | `google/veo-3.1-lite` (~$0.30 for 6 s with audio at 720p) | `google/veo-3.1` (~$3.20 for 8 s at 1080p with audio) |
| People, motion, action; animating a photo | `kwaivgi/kling-v3.0-pro` (~$0.56) | Strong motion; first- and last-frame control; 3 to 15 s; negative prompts | `kwaivgi/kling-v3.0-std` (~$0.42) | Kling Pro with audio (~$0.84) |
| Same character across several shots | `bytedance/seedance-2.0` (~$0.76) | Described as particularly strong at character consistency; takes reference images | `bytedance/seedance-2.0-fast` (~$0.45) or `-mini` (~$0.38) | `bytedance/seedance-2.5` (~$1.15; long-form, editing and extending, up to 30 s) |
| Long single clip (15 to 30 s) | `bytedance/seedance-2.5` or `alibaba/wan-3.0` (~$0.50 at 720p) | Both go to 30 s | `bytedance/seedance-2.5-flash` | `alibaba/wan-3.0-prime` |
| Polished, cinematic look | `runway/gen-4.5` (12 c/s; 2 to 10 s, 720p, 16:9 or 9:16) | Prompt adherence, motion quality | | |
| High resolution (2K or 4K) | `black-forest-labs/flux-3-video` (17 to 41 c/s) | Up to 4K, opening and closing keyframes | `minimax/hailuo-3` (2K, ~$0.65) | `google/veo-3.1` at 4K |
| Fast and cheap experiments | `x-ai/grok-imagine-video` (5 c/s at 480p) | 1 to 15 s, very cheap | `grok-imagine-video-1.5-lite` (2 c/s at 480p) | `x-ai/grok-imagine-video-1.5` |
| Text or logos inside the video | `minimax/hailuo-3` | Described as good at text and brand rendering | | |
| Talking head from one photo (lip-sync) | `heygen/avatar-iv` (5 c/s) | Photo plus script becomes a talking video; voice options via `--option` | | |
| Short clip with built-in dialogue and SFX | `heygen/heygen-video-1` | Synthesised audio in one call | | |
| Edit an existing video (swap object, restyle, change setting) | `black-forest-labs/flux-video-edit` (3 c/s) | Instruction-based edits | | `runway/aleph-2` (28 c/s, minimum 56 c) |
| Upscale a video | `black-forest-labs/flux-video-upscale` | 1.5 to 3 times larger, same length | | |
| Extend or continue a clip | A model that accepts `--extend JOB_ID` (Seedance 2.5, FLUX.3 Video) | Continues the same shot | | |

Notes:
- **Veo** accepts only 4, 6 or 8 seconds and only 16:9 or 9:16.
- **Kling** offers 16:9, 9:16 or 1:1 at 720p only.
- **Runway Gen-4.5** is 720p only.
- **Seedance** is priced per "video token", so the estimate is approximate. Trust the "Actual cost" line.
- **Image to video** is usually the best way to get a specific look. Make the frame with an image
  model first, then animate it.
- **Provider options** (negative prompt, guidance and so on) need the provider's slug, for example
  `--option google-vertex.negativePrompt="blurry"` for Veo. Other slugs (Kling, Seedance's `seed`
  or `byteplus`) aren't listed by the API. Try one, and if the option is ignored, put the
  guidance in the prompt instead.

## Images

| Job | First choice | Approx. cost | Notes |
|---|---|---|---|
| General use, edits, combining several pictures | `google/gemini-3.1-flash-image` (Nano Banana 2) | ~$0.07 | Up to 14 reference images; 512 to 4K |
| Best quality, complex scenes, text, real-world accuracy | `google/gemini-3-pro-image` (Nano Banana Pro) | ~$0.13 to $0.25 | |
| Precise edits, dense layouts and text, consistent multi-step edits | `openai/gpt-image-2.6-sunburst` | ~$0.03 to $0.15 by quality | Up to 16 references; `--quality low/medium/high` |
| Fast iterations | `openai/gpt-image-2.6-flare` or `google/gemini-3.1-flash-lite-image` | ~$0.02 to $0.04 | |
| Photoreal products and lifestyle shots | `bytedance-seed/seedream-5-5` | $0.02 to $0.035 | Up to 10 references |
| Cheapest decent drafts | `black-forest-labs/flux.2-klein-4b` | ~$0.015 per megapixel | Up to 4 references |
| Top artistic quality | `black-forest-labs/flux-3-image` | $0.04 to $0.10 (4K ~$0.60) | Up to 10 references |
| Logos, icons, illustration, SVG | `recraft/recraft-v4.1-vector` | $0.08 | Outputs SVG |
| Text-accurate posters and graphics | `qwen/qwen-image-3` | $0.03 | Small text down to 10 px |
| Edit one photo with instructions | `krea/k3-edit` | $0.03 to $0.06 | Needs 1 to 8 input images |
| 360° panorama | `tencent/hy-world-2.1-panorama` | | |

For a video's first frame, make the image at the **same aspect ratio** as the video you plan.
