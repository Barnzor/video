# Recipes

Multi-step workflows for the results people usually want from tools like Higgsfield. In all of
them, `S` is `python3 .claude/skills/openrouter-studio/scripts/studio.py`. Show the plan and the
total cost before you start, and show each intermediate image so the user can redirect early.

## Animate a photo (the most controllable way to get a specific look)
1. If the user has no photo, make the first frame: `S image --model google/gemini-3.1-flash-image --aspect 9:16 --prompt "..."`.
   Make 2 to 4 options with `--n` or separate calls, and let the user pick.
2. Animate it: `S video --model kwaivgi/kling-v3.0-pro --first-frame outputs/<pick>.png --aspect 9:16 --duration 5 --prompt "<motion and camera only>"`.

## Start-to-end transition or morph
1. Make or get two images, a start and an end, at the same aspect ratio.
2. `S video --model kwaivgi/kling-v3.0-pro --first-frame start.png --last-frame end.png --duration 5 --prompt "Smooth continuous transformation from ... into ..., camera slowly orbits"`.
   Other models with last-frame support include Veo 3.1, Seedance, Wan 3.0, Hailuo 3 and FLUX.3 Video.

## Consistent character across several shots
1. Make a **character sheet** first: one image of the character, front-facing and evenly lit on
   a plain background. Optionally make a second image with a turnaround (front, side, back).
2. For each shot, make the shot's first frame **with the sheet as a reference**:
   `S image --model google/gemini-3.1-flash-image --ref outputs/character.png --prompt "The same woman from the reference, now sitting in a café ..."`.
3. Animate each frame with the **same video model and style words** each time. Seedance 2.0 is
   described as the strongest at character consistency; you can also pass the sheet with
   `--ref outputs/character.png`.
4. Keep a running "character line" (for example, "30-year-old woman, short copper hair, green
   raincoat") and paste it into every prompt.

## Product ad (UGC or studio style)
1. Get a clean product photo from the user. Better still, a cutout on a plain background.
2. Make 2 or 3 hero frames that put the product in a scene:
   `S image --model bytedance-seed/seedream-5-5 --ref product.png --aspect 9:16 --prompt "The bottle from the reference on a sunlit bathroom shelf, ..."`.
   Remind the model to keep the label and shape exactly the same.
3. Animate with a slow, premium camera move ("slow orbit", "push-in with rack focus").
   Product ads usually look best calm.
4. Variations: change the setting or time of day, and keep the product reference the same.
5. Check the label text in every frame. Models often garble it. If they do, use a shot where the
   label is less legible, or edit the frame with `openai/gpt-image-2.6-sunburst` first.

## Talking head / spokesperson from one photo
- `S video --model heygen/avatar-iv --first-frame face.jpg --prompt "<the script to speak>" --aspect 9:16`.
  The voice and style options (`voice_id`, `expressiveness`, `background`, `caption`) are
  provider options. If they're needed, try `--option heygen.voice_id=...`.
- For a whole scene with dialogue (not a single talking face), use Veo 3.1 with `--audio` and
  put the line in quotes in the prompt.
- Only use a real person's face with their permission.

## Short story or ad sequence (several clips)
1. Write a shot list together with the user: 3 to 6 shots, each one action, each 4 to 8 seconds.
2. Lock the look: aspect ratio, style words, character line and colour grade, the same in every prompt.
3. Make all the first frames as images and get approval of the set (cheap).
4. Animate the approved frames. Run them in parallel with `--no-wait`, then `wait` on each job.
5. Join them, with optional music, using ffmpeg:
   ```
   printf "file '%s'\n" outputs/shot1.mp4 outputs/shot2.mp4 > /tmp/list.txt
   ffmpeg -f concat -safe 0 -i /tmp/list.txt -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac outputs/final.mp4
   ```
   If the clips differ in size or audio, normalise them first: add
   `-vf scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2`
   and give silent clips a silent audio track.

## Edit, extend or upscale a video
- **Edit** (swap an object, restyle, change the setting): `S video --model black-forest-labs/flux-video-edit --ref-video <video URL or file> --prompt "Replace the red car with a white vintage van; keep everything else"`.
- **Extend** a clip made here: `S video --model <same model> --extend <JOB_ID from history> --prompt "<what happens next>"`.
  Only continuation-capable models accept this (Seedance 2.5, FLUX.3 Video). Others will error.
- **Upscale**: `S video --model black-forest-labs/flux-video-upscale --ref-video <video>`.
  Upscaling uses its own settings; if the request is rejected, read the error and adjust.
- Large local videos may be too big to send inline. If a call fails because of size, ask the
  user for a public link to the video.

## Higgsfield-style camera effects
There are no presets here, but most effects are just a camera move plus motion. Put them in the
prompt (image to video works best):

| Effect | Prompt wording |
|---|---|
| Crash zoom | "sudden fast crash zoom into her eyes" |
| Dolly zoom (vertigo) | "dolly zoom: camera moves back while zooming in, background stretches" |
| Bullet time | "time freezes, camera orbits 180° around the subject frozen mid-air" |
| FPV drone | "FPV drone shot diving fast through the canyon, banking turns" |
| 360 orbit | "camera orbits a full 360° around the subject, smooth" |
| Crane up / reveal | "camera cranes up and back to reveal the whole city" |
| Snorricam | "camera locked to the subject's chest while they walk, background swings" |
| Through-object | "camera flies through the keyhole into the room" |
| Disintegration | "the figure disintegrates into drifting particles of ash" |
| Turn into / morph | Use the start-to-end recipe with two frames |

## Check a video (do this before asking the user if it's right)
Pull 4 frames and look at them:
```
ffmpeg -loglevel error -i outputs/clip.mp4 -vf "select='not(mod(n\,30))',scale=480:-1" -frames:v 4 -vsync vfr /tmp/frame-%02d.png
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 outputs/clip.mp4
```
Read the PNGs, and check the subject, the action, the framing, any warping, text, and the aspect
ratio against the brief.
