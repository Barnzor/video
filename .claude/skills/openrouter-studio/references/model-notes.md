# Per-model notes: syntax, limits and quirks

Taken from the November 2026 research report. **OpenRouter's live listings decide what can be
sent**: check with `models video|image --search <name>`, which shows the durations, resolutions
and "extra options". These notes decide **how to word it**. "3P" means the source was
third-party documentation, not the vendor.

Extra options go in an item's `options` as `"<provider-slug>.<option>": value`. The extra
option names below are from OpenRouter's listing. **Provider slugs are mostly unconfirmed**:
`google-vertex` for Veo is documented, the rest are guesses. Treat any extra option as
unverified until a take shows its effect, and don't let a plan depend on one.

## Video models

### Google Veo 3.1 / Fast / Lite (`google/veo-3.1*`)
- **Formula:** [Cinematography] + [Subject] + [Action] + [Context] + [Style & ambiance], in English prose.
- **One focused moment per clip.** Chaining events gives "muddled" results. Use timestamp
  segments `[00:00-00:02] …` (up to about 4 in 8 s) only for deliberate quick sequences.
- **Dialogue:**
  - Use a colon, not quotes, because quotes can put the words on screen: `The woman in the red coat says: We're almost there.`
  - Keep it to about 15–20 words per 8 s.
  - Add "(no subtitles)".
  - Spell hard names phonetically.
  - Tag speakers by appearance.
  - Subtitles still appear on a share of takes. Plan to crop the bottom 10–15% or reroll.
- **Unwanted talking:** use "lips closed", give the character a visible action, describe the
  ambience, and avoid framing them face-on to camera.
- **Audio** goes in separate sentences labelled `SFX:` and `Ambient noise:`. Describe the
  ambience, or it may invent a studio audience.
- **Exploring options:** seeds change little, so change the wording instead. Rerolling mostly fixes glitches.
- **Image to video:** motion only. First and last frames are both supported. Reference images
  (up to 3) **force 8 s** on standard; Lite accepts none. Phrase it as "Using the provided
  images for the detective and the office…".
- **Settings:** 4, 6 or 8 s only, 16:9 or 9:16 only.
- **Extra options listed:** `negativePrompt`, `enhancePrompt`, `personGeneration`,
  `conditioningScale` (slug `google-vertex`, inside `parameters`, which the script handles).
  These are untested through OpenRouter. The report found OpenRouter's own Veo page lists no
  negative or enhance parameter. Keep positive wording in the main prompt regardless.
- **Default rewriter:** `enhancePrompt` is on by default on Google's side. A full, precise
  prompt leaves it little to change.

### Kling 3.0 Pro / Std, Kling O1 (`kwaivgi/kling-*`)
- **Formula:** Subject + Action + Scene + Camera + Lighting/mood. Use **simple words and short sentences**.
- **Tempo words matter:** slow (intimate, suspense), steady (readable action), quick (energy).
  Add "real-time speed" for action, because dramatic action tends to come out in slow motion
  (one tester's report).
- **Multi-shot:** `[Shot 1: Wide shot] …` blocks, or describe the coverage and let it choose.
- **Dialogue:** keep each speaker's name, line and delivery together. Supports English,
  Chinese, Japanese, Korean and Spanish.
- **Weak on exact counts and complex physics** (bouncing or thrown objects).
- Words like "Oriental" or "Asia" push the styling Chinese.
- **Best first/last-frame fidelity** in one practitioner test.
- Settings: 720p; 16:9, 9:16 or 1:1; 3–15 s.
- **Extra options listed:** `negative_prompt` (a short artifact list such as "morphing,
  warping, extra fingers, text"), `cfg_scale`. The slug is unconfirmed.
- No official O1 guide exists. Assume the 3.0 rules apply.

### ByteDance Seedance 2.0 / Fast / Mini / 2.5 / 2.5 Flash (`bytedance/seedance-*`)
- **Formula:** the subject and its motion are required, with concrete verbs. Environment, look,
  camera and audio are optional layers. Swap mood words ("beautiful", "cinematic") for a
  specific subject, move and sound.
- **Emotion:** pair each emotion word with 2–4 visible cues (brows, mouth, breathing, gaze,
  hands) and the event that triggers it.
- **Camera:** name what the camera follows or orbits, and where the move starts and ends.
  Describe rare techniques by what they look like, e.g. "foreground softens while background sharpens".
- **Multi-shot:** use "Shot 1 … cut to Shot 2 …" on 2.0, and timestamps on 2.5. Timestamps are
  time budgets, not exact cuts. For long clips, use stages with one change each, plus a
  "consistency block" covering identity, clothing, props and screen direction.
- **References:** `@Image1`-style roles. Declare first/last frames in the opening line, e.g.
  "@Image 1 is the first frame…", and add "Do not use…" lines per reference. Stability drops
  as references are added.
- **Audio:**
  - Say "no music" or "no voiceover", or it may add an orchestral score.
  - Name the dialogue language first ("Dialogue language: American English."), or English may come out spoken in Chinese.
  - On 2.5, use `()` for music, `<>` for SFX, `{}` for dialogue, `【】` for subtitles.
  - Keep lines short, because long monologues drift out of lip sync.
- **Extra options listed:** `watermark` (e.g. false), `return_last_frame` (Mini).
  The slug might be `seed` or `byteplus` (unconfirmed).
- **Routing:** the longest clips, the most references and cheap B-roll. Stated to be strong at character consistency.

### Runway Gen-4.5 (`runway/gen-4.5`) and Aleph 2 (`runway/aleph-2`)
- **Gen-4.5:**
  - Start simple and add one element at a time, in plain visual prose with no requests.
  - Image to video: **motion only**. Always say what doesn't move, e.g. "the camera holds completely still".
  - No negatives. About 1,000 characters (3P). One first frame only. 720p; 16:9 or 9:16.
- **Aleph (editing an existing video):**
  - Start with a verb (change, replace, add, remove, restyle or relight), name the target and
    the new state, then end with "keep everything else unchanged". Anything not mentioned can change.
  - Edit separate shots separately. It can't invent new scenes.

### Alibaba Wan 2.6 / 2.7 / 3.0 / 3.0 Prime (`alibaba/wan-*`)
- **Order (3.0):**
  1. overall description (theme, perspective, mood, pacing)
  2. reference citations
  3. timed shot blocks
  4. dialogue
  5. sound effects and music
  6. style
  7. negatives
- **Multi-shot:** `Shot 1 [0–3 s] …` with "Hard cut" or "Dissolve", in segments of 2–5 s with no gaps.
  For one continuous shot, write **"Generate a single-shot video."**, or it may cut.
- **Locked camera:** "Fixed shot, camera static, position unchanged." Keep orbits under 45°.
- **Dialogue:**
  - Use unique character labels, never pronouns.
  - Put each character's action before their line, written `Label says: "…"`.
  - Describe the voice as emotion, tone, speed, timbre and accent.
  - Write "No dialogue." and "No background music." to switch those off.
  - On 3.0, the keyword "Lip sync" is available.
- **References:** "Image 1 / Video 1 / Audio 1" with explicit roles, plus a role-lock sentence.
- **Avoid:** named real people, rapid scene changes, exact readable text, long action sequences.
- **Extra options listed:**
  - 2.6: `negative_prompt`, `enable_prompt_expansion` (set false), `shot_type`, `audio`.
  - 2.7: `negative_prompt`, `prompt_extend` (set false), `audio`, `last_image`.
  - 3.0: none.

  Rewriters default to on. Turn them off for precise prompts if the option works.

### MiniMax Hailuo 2.3 / Hailuo 3 / 3 Max (`minimax/hailuo-*`)
- **Hailuo 2.3:**
  - It has 15 bracket camera commands in exact casing: `[Push in]`, `[Pull out]`, `[Pan left]`,
    `[Pan right]`, `[Tilt up]`, `[Tilt down]`, `[Truck left]`, `[Truck right]`, `[Pedestal up]`,
    `[Pedestal down]`, `[Zoom in]`, `[Zoom out]`, `[Shake]`, `[Tracking shot]`, `[Static shot]`.
  - Commands inside one bracket run together (at most 3). Separate brackets run in sequence,
    e.g. "A man picks up a book [Pedestal up], then reads [Static shot]."
  - These commands beat plain-language camera directions, but distance and speed are approximate.
  - No audio and no multi-shot. 6 or 10 s at 768p; 6 s at 1080p.
- **Extra options listed:** `prompt_optimizer` (**set false** for exact control; the vendor
  says so), `fast_pretreatment`. On Hailuo 3, `aigc_watermark`.
- **Hailuo 3 / H3:** first/last frame, references called "reference image 1". Stated to be good
  at text and brand rendering.

### xAI Grok Imagine Video / 1.5 / 1.5 Lite (`x-ai/grok-imagine-video*`)
- Write a compact paragraph covering subject, action, camera movement and mood. Over-long
  prompts return an error.
- **Always set the resolution**, because the default is 480p.
- Audio is on by default, so include an audio block.
- In image to video, the output takes the image's aspect ratio. 1.5 supports up to 4 keyframes.

### HeyGen Avatar IV (`heygen/avatar-iv`) and HeyGen Video (`heygen/heygen-video-1`)
- **Avatar IV:**
  - Input: a well-lit close-up or half-body photo, with the face filling the frame and a
    subtle (not wide) smile.
  - The prompt is the **script**. Pace it with punctuation: commas for short pauses, full stops
    for breaks, "…" for longer pauses.
  - Motion follows "[Body part] + [Action] + [Emotion or intensity]", e.g. "Right arm raises in
    a wave, enthusiastic and friendly." Use one gesture, or at most two clauses. No timing,
    camera moves, scene changes or walking.
  - Custom motion loops after 10 s.
  - **Extra options listed:** `voice_id`, `voice_settings`, `motion_prompt`, `expressiveness`,
    `background`, `remove_background`, `caption`, `fit`. The slug is unconfirmed.
- **HeyGen Video:** generates clips with built-in dialogue and sound effects. Option `prompt_enhancement`.

### Black Forest Labs FLUX.3 Video, Video Edit, Video Upscale
- **FLUX.3 Video:**
  - Write "[camera] shot of [subject] [action] in [environment]. [details]". Direct a scene;
    don't list objects.
  - Use 2–3 beats per 5 s. For multi-shot, write `SHOT ONE: … HARD CUT. SHOT TWO: …`, keeping
    the subject description identical across shots and global style last.
  - Dialogue in quotes. Physical sound sources (footsteps, rain) come out clearest.
  - Audio is on by default. Options `draft`, `version`, `safety_tolerance`.
- **Video Edit:**
  - Takes only the video and a prompt. Anything not mentioned stays as shot.
  - Use "Remove the orange bucket." or "Replace X with Y".
  - Edit in stages. The source must be 15 s or shorter.
  - A replacement line can't be longer than the original speech.
- **Video Upscale:** OpenRouter lists 15 s and 50 MB. Trust OpenRouter's limits.

## Image models

### Google Nano Banana family (`google/gemini-*-image*`, `google/gemini-nano-banana-2.1`)
- **Prose:**
  - Open with a strong verb, then subject, action, location, composition and style.
  - State the purpose and audience.
  - It also follows Markdown rule lists and capitalised MUST/NEVER constraints well.
- **Pro** leans toward realism, so state a stylised look first and forcefully. It's the best for
  dense text, and handles character-sheet grids up to about 4×4.
- **Nano Banana 2 / Flash** is faster and cheaper, but looser: it may add taglines or substitutions.
- **Edits:** "Using the provided image, change only the [element] to [new element]. Keep
  everything else in the image exactly the same, preserving the original style, lighting, and
  composition." It's very good at local edits, but repeated edits drift, so re-anchor.
- **References:** up to 14. Give each a role: "Use image A for the pose, image B for the art style".
- **Aspect ratio:** state it in the prompt **and** the `aspect` setting.
- **Text:** settle the wording first, then quote it exactly with a named font.
- **Video:** this is Google's documented keyframe engine for Veo.

### OpenAI GPT Image 2 / 2.5 / 2.6 Flare and Sunburst (`openai/gpt-image-*`)
- **Structure:** intended use first, then scene, subject, details and constraints. Use labelled
  sections for complex images.
- **Text:**
  - Quote it and spell unusual words letter by letter.
  - Say it "appears once" and add "no extra text".
  - Use `quality: high` for small text. OpenRouter's quality setting stops at high.
- **Edits:** restate the keep-list every turn rather than adding new instructions. Short "Do
  not…" clauses work.
- **Choosing a version:** Sunburst for precision and dense layouts, Flare for speed.
- gpt-image-1 is retired, and 1.5 shuts down on 1 Dec 2026.

### Black Forest Labs FLUX.2 / FLUX 3 (`black-forest-labs/flux*`)
- **Length and order:** 30–80 words, front-loaded, because earlier words weigh more. JSON works
  as well as prose.
- **No negatives at all.** Use the replacement method: ask what fills the space.
- **Edits:** identify the target uniquely, state the change, then name each element to keep.
  Keep that list short and after the edit.
- **References:** image 1 sets the aspect ratio. FLUX.2 Pro takes about 8, FLUX 3 up to 10.
- **FLUX 3:** no seed, so run a prompt twice before judging a change. Klein's automatic prompt
  expansion should stay on. Changing resolution recomposes the image.
- **Colours:** hex codes tied to an object work.

### ByteDance Seedream 4.5 / 5.0 / 5.5 (`bytedance-seed/seedream-*`)
- Use concise, precise prose with the purpose stated. Put text in double quotes.
- **Edits:** say "keeping its pose unchanged" and avoid vague pronouns. Edits can introduce
  small unwanted changes, so check details.
- Saying "a series" or giving a number can produce a set of images.
- Strong on photoreal product texture. 5.0 Pro handles dense multilingual text.

### Qwen Image (`qwen/qwen-image-*`)
- Write prose. It's the strongest at Chinese text.
- 1–3 reference images, called "Image 1/2/3". **The output takes the last image's aspect ratio.**
- Has a `negative_prompt` field and `prompt_extend` (on by default; turn it off for exact wording).

### Recraft V4 / V4.1 (`recraft/recraft-*`)
- 3–6 words gives "interpretive mode". For control, follow this order: core concept,
  background, framing, attributes, lighting, camera, mood.
- Describe the typography system and quote all text.
- Reference images transfer **style only**, not content.
- V4 has no negative field, so put exclusions in the prompt ("no gradients, shadows, or texture").
- Vector variants output SVG. Best for logos, icons and designed type.
