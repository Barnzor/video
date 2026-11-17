# Writing prompts that get the shot

## The standard: no gaps

A model fills every gap you leave with its own guess. That's how unwanted people, random
lettering, extra objects and odd camera moves appear. So every prompt in a plan must pass this
checklist before it is shown to the user. There are no exceptions, not even for tests.

| # | Must state | Example |
|---|---|---|
| 1 | **Shot and camera:** framing, lens, height, and the move (or "locked-off") | "Wide shot, 35mm, eye level just above the waterline, slow push-in" |
| 2 | **Subject:** what exactly, with 3 or more concrete details (material, colour, size, condition, clothing, age) | "small wooden sailboat, honey-varnished planks, single cream canvas sail" |
| 3 | **Count and emptiness:** how many of each thing, and who is **not** there | "one boat, alone; empty, nobody aboard" |
| 4 | **Action and timing** (video): one main action, its pace, and where it ends | "rocks gently on slow swells; sail ripples; ends still centred" |
| 5 | **Setting:** place, background, time of day, weather | "open calm sea, distant flat horizon, golden hour, clear air" |
| 6 | **Light and colour:** direction, quality, palette | "low sun behind camera left, warm rim light on the sail, peach-and-gold sky, turquoise water" |
| 7 | **Composition:** where the subject sits, what's in the background, and the space needed for text or overlays | "boat centred in the lower half, horizon on the upper third" |
| 8 | **Style and finish:** medium and texture | "photoreal, natural colours, fine film grain" |
| 9 | **Text and marks:** the exact words in quotes, or say there are none | "clean, unmarked hull; no text anywhere" |
| 10 | **Sound** (video with audio on): ambience, effects, music mood, and dialogue with its speaker | "soft lapping water, light wind, no music" |
| 11 | **Keep fixed** (image to video, and edits): what must not change | "the boat, sail and colours stay exactly as in the start frame" |
| 12 | **Avoid:** the known failure modes for this shot | see below |

**How to write "avoid":**
- Prefer **positive wording** in the main prompt ("empty boat", "clean unmarked hull",
  "single subject"). Some models read "no people" as a hint to add people.
- When the model has a negative-prompt option, also put the avoid list there. For Kling, use
  `"options": {"kling.negative_prompt": "..."}` (the slug may need confirming). For Veo, use
  `"options": {"google-vertex.negativePrompt": "..."}`. For Wan, use `negative_prompt`.
- Typical avoid lists:
  - **People shots:** extra fingers, warped hands, face changing, extra people.
  - **Products:** changed label, garbled text, wrong logo, extra items.
  - **Scenes:** random text or signage, watermarks, people in the background, cuts, sudden camera shake.

**Length:** images 60 to 150 words; video 50 to 120 words. For **image to video**, items 1, 4, 10
and 11 matter most, because the picture already settles the look, and restating the look can
fight the image. When showing the plan, tell the user in one line which checklist points you
deliberately left to the model, if any.

**Worked example (the sailboat test, done properly):**

*Image:* "Cinematic wide shot, 35mm lens at eye level just above the waterline. One small wooden
sailboat with honey-varnished planks and a single cream canvas sail floats alone in the centre of
the lower half of the frame on a calm turquoise sea. The boat is empty with a clean, unmarked hull.
Gentle ripples, a soft reflection beneath the hull. Open sea to a flat horizon on the upper third,
peach-and-gold sky at golden hour, low sun behind camera left giving warm rim light on the sail.
Photoreal, natural colours, fine film grain, light haze on the horizon. No text anywhere."

*Video (from that image):* "Slow, steady push-in toward the boat across the whole clip, camera
level. The boat rocks gently on slow swells, the sail ripples softly in a light breeze, and
sunlight glitters on the water. The boat, sail, colours and empty deck stay exactly as in the
start frame. Smooth, calm motion, one continuous shot." The negative prompt, if the model
supports one, would be: "people, text, letters, extra boats, cuts, camera shake".

## Video: write one shot, like a cinematographer

Use this order, in one paragraph of 40 to 120 words:

1. **Shot and camera.** The framing and the move, for example: "Slow dolly-in, medium close-up,
   35mm, shallow depth of field."
2. **Subject.** Who or what, with 2 or 3 concrete details: age, clothing, material, colour.
3. **Action.** One main action, with a verb and a pace: "turns her head toward the window and
   smiles slowly."
4. **Setting.** Place, time of day, weather and background activity.
5. **Light and colour.** "Warm golden-hour backlight, soft haze, teal-and-orange grade."
6. **Style.** "Photoreal, filmic grain", "Pixar-style 3D", "anime cel shading", "handheld documentary".
7. **Sound.** Only when audio is on: ambience, sound effects, music mood, or a line of dialogue in
   quotes with who says it: *The barista says: "Your usual?"*

**Do:**
- Use one action per clip. Make a sequence as separate clips.
- Describe the camera explicitly. Useful terms: static, pan left/right, tilt up/down, dolly
  in/out, tracking shot, orbit, crane up, drone fly-over, handheld, whip pan, push-in, rack
  focus, slow motion, timelapse.
- Use concrete, visual words. "Rain-slicked neon street at night" beats "a cool city".
- Match the length to the action. A head turn needs 4 to 5 seconds; a walk across a room needs 8.
- When animating a photo, **describe only the motion and the camera**. The picture already
  defines how things look, and restating it can fight the image.

**Don't:**
- Stack several actions or scene changes in one clip.
- Ask for readable text, logos or exact counts unless the model is good at it. See the models
  file: Hailuo 3 and Veo do better.
- Use vague quality words alone ("4K, masterpiece, best quality"). They do little.
- Name copyrighted characters or real people without the user's say-so.

**Example (text to video):**
> Slow push-in, medium shot, 35mm. A young chef in a white apron flips vegetables in a flaming
> wok; sparks and steam rise. A cramped night-market stall, strings of bulbs, a blurred crowd
> behind. Warm tungsten light with blue night ambience, shallow depth of field, photoreal with
> light film grain. Sizzling wok, crowd chatter, distant scooter horns.

**Example (image to video):**
> The woman slowly turns from the window toward the camera and smiles; her hair drifts in a light
> breeze. Gentle handheld push-in. Dust motes float in the sunlight.

## Images

Give the subject, then the composition, setting, light, style, and purpose or format:

> Product photo of a matte black water bottle on wet slate, three-quarter view, centred with
> negative space on the left for text, soft overcast daylight, fine water droplets, commercial
> studio look, 4:5.

- For **edits**, say what to change and what to keep: "Change the jacket to red leather. Keep
  the face, pose, lighting and background exactly the same."
- For **combining references**, say which picture supplies what: "Put the person from image 1
  in the setting of image 2, wearing the jacket from image 3."
- For **text in images**, put the exact words in quotes and name the font style and placement.

## Iterating

- **Wrong look:** change the style and lighting words, or make a first-frame image and animate it.
- **Wrong motion:** simplify to one action, name the camera move, or change the length.
- **Subject changes during the clip:** use image to video, a reference image, or Seedance or Kling.
- **Too much movement or warping:** ask for a "subtle", "slow" or "static camera" version, and
  shorten the clip.
- **Almost right:** keep the same prompt and seed (where supported), and change one thing.
