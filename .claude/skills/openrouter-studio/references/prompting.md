# Writing prompts that get the shot

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
