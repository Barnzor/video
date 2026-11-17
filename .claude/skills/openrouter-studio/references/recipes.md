# Recipes

Multi-step workflows for the results people usually want from tools like Higgsfield. Each one
is a **plan shape**: the items to put in `plan.json`, and the rounds to approve them in. Every
item still goes through show, approve and run (see SKILL.md). Show each round's results before
planning the next, so the user can redirect early.

## Animate a photo (the most controllable way to get a specific look)
- **Round 1:** if the user has no photo, add 2 to 4 image items (`frame1a`, `frame1b`, and so
  on) for the first frame. Use different wording or models, at the video's aspect ratio, with
  `google/gemini-3.1-flash-image`. The user picks one.
- **Round 2:** a video item with `"inputs": {"first_frame": "@frame1b"}` (or the user's file),
  e.g. `kwaivgi/kling-v3.0-pro`, with a prompt that describes **motion and camera only**.

## Start-to-end transition or morph
- Two image items (`start`, `end`) at the same aspect ratio, or the user's own files.
- A video item with `"inputs": {"first_frame": "@start", "last_frame": "@end"}` and a prompt like
  "Smooth continuous transformation from ... into ..., camera slowly orbits".
- Models with last-frame support include Kling 3.0, Veo 3.1, Seedance, Wan 3.0, Hailuo 3 and
  FLUX.3 Video.

## Consistent character across several shots
- **Round 1:** a `character` image item. One image of the character, front-facing and evenly lit
  on a plain background. Optionally add a `turnaround` item (front, side, back) with
  `"refs": ["@character"]`.
- **Round 2:** one first-frame image item per shot, each with `"refs": ["@character"]` and a
  prompt like "The same woman from the reference, now sitting in a café ...".
- **Round 3:** a video item per shot. Use the **same video model and style words** for every
  shot. Seedance 2.0 is described as the strongest at consistency, and can also take
  `"refs": ["@character"]`.
- Write a fixed "character line" (e.g. "30-year-old woman, short copper hair, green raincoat")
  into the brief, and paste it word for word into every prompt.

## Product ad (UGC or studio style)
- Ask the user for a clean product photo. Better still, a cutout on a plain background.
- **Round 1:** 2 or 3 hero-frame image items with `"refs": ["product.png"]`, e.g. using
  `bytedance-seed/seedream-5-5`. Each prompt puts the product in a scene and says to keep the
  label and shape exactly the same.
- **Round 2:** video items with slow, premium camera moves ("slow orbit", "push-in with rack
  focus"). Product ads usually look best calm.
- Check the label text in every take, because models often garble it. If one does, plan a fix
  item: an edit with `openai/gpt-image-2.6-sunburst` and `"refs": ["@hero1"]`.

## Talking head / spokesperson from one photo
- A video item on `heygen/avatar-iv` with `"first_frame": "face.jpg"`. The prompt is **the script
  to speak**, the same words as in the plan's `script`. Voice and style choices (`voice_id`,
  `expressiveness`, `background`, `caption`) are provider options. If they're needed, try
  `"options": {"heygen.voice_id": "..."}`.
- For a whole scene with dialogue (not a single talking face), use Veo 3.1 with `"audio": true`.
  Write the line after a colon, not in quotes: `The man in the grey suit says: …`. Keep it to
  about 15–20 words per 8 s, and add "(no subtitles)". See model-notes.
- Creators often avoid on-camera speech altogether, because it's where the "AI look" shows most.
  They put the words in a voice-over instead, made separately.
- Only use a real person's face with their permission.

## Short story or ad sequence (several clips)
1. Agree the **script** and a **shot list** with the user: 3 to 6 shots, each with one action,
   each 4 to 8 seconds. Both go into the plan, as `script` and as one item per shot.
2. Lock the look in the brief: aspect ratio, style words, character line and colour grade. Use
   the same wording in every prompt.
3. **Round 1:** all the first frames (cheap). **Round 2:** all the videos. **Round 3:** redo
   any shot that's not right.
4. Finishing touches (free, no API): join the chosen takes with ffmpeg, add music or captions if
   the user supplies them. Describe these steps in the plan's brief too.
   ```
   printf "file '%s'\n" shot1-take1.mp4 shot2-take2.mp4 > list.txt
   ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac final.mp4
   ```
   If the clips differ in size or audio, normalise them first: add
   `-vf scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2`
   and give silent clips a silent audio track.

## Edit, extend or upscale a video
- **Edit** (swap an object, restyle, change the setting): a video item on
  `black-forest-labs/flux-video-edit` with `"ref_videos": ["@shot1"]` (or a file or URL), and a
  prompt like "Replace the red car with a white vintage van; keep everything else".
- **Extend:** a video item on the **same model** with `"extend": "@shot1"`, and a prompt
  describing what happens next. Only continuation-capable models accept this (Seedance 2.5 and
  FLUX.3 Video).
- **Upscale:** a video item on `black-forest-labs/flux-video-upscale` with `"ref_videos": ["@shot1"]`.
- Large local videos may be too big to send inline. If a run fails because of size, ask the
  user for a public link to the video.

## Higgsfield-style camera effects
There are no presets here, but most effects are just a camera move plus motion, written into the
prompt. They work best with image to video:

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
| Turn into / morph | Use the start-to-end recipe |

## Check a video (do this before asking the user if it's right)
Pull 4 frames and look at them:
```
ffmpeg -loglevel error -i shot1-take1.mp4 -vf "select='not(mod(n\,30))',scale=480:-1" -frames:v 4 -vsync vfr /tmp/frame-%02d.png
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 shot1-take1.mp4
```
Read the PNGs, and check the subject, the action, the framing, any warping, text, and the aspect
ratio against the plan.
