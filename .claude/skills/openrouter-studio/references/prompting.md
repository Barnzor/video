# How to write prompts that get the shot

Based on the November 2026 research report: official guides from Google, Kling, ByteDance,
Alibaba, Runway, BFL, OpenAI and Recraft, plus creator and user evidence. Model-specific syntax
and limits are in `model-notes.md`. Read the notes for each model you plan to use.

## The big idea

The prompt itself is a fairly solved problem. Every vendor teaches the same five-part brief. What
separates good results from bad is **control of the inputs and the loop**:
- locked still frames,
- end frames made by editing start frames,
- references with clear roles,
- character descriptions pasted word for word,
- rewriters off when the prompt is already precise,
- a retake budget that triggers a redesign instead of endless rerolls.

Magic words ("8k, masterpiece, ultra-detailed") are obsolete. They push images toward a fake CGI look.

## Universal rules

1. **Write prose, not keyword lists.** Google calls lists "tag soup". Comma-separated tags belong
   only in a real negative-prompt field.
2. **Front-load.** Lead with the shot, the subject and the action. Several models weight earlier
   words more. To get a non-default look (anime, claymation, 16mm), put the style **first**:
   "In the style of a 1970s 16mm documentary: …".
3. **State the purpose.** "A hero image for a minimalist skincare brand's homepage" beats "a
   product photo". The model infers styling from the purpose.
4. **Use rich nouns but a light load.** Specific materials, light direction, lens and texture
   help. Extra actions, extra camera moves and stacked adjectives hurt.
5. **One clip: one moment, one action, one camera move.** This has the strongest creator
   agreement. Stacked camera moves are the main cause of jitter.
6. **Every camera move needs three things:** the named move, its speed, and its end framing.
   Example: "Slow dolly-in toward her face, constant speed, settling into a static close-up."
   - With no camera direction, you usually get a static wide shot.
   - Keep orbits under about 45°.
   - "Dolly" means the camera moves; "zoom" means the lens changes. Don't mix them up.
7. **Avoid exact counts.** Models are poor above about 3. Write "a small group", or control the
   number with a reference image.
8. **Every video prompt ends with an audio block.** That applies even when silent ("Ambience:
   soft wind. No music."), because models invent sound otherwise, such as random orchestral
   scores or studio audiences. Only skip it on models with no audio (see model-notes).
9. **No pleasantries.** "Please" and "make a video of" add nothing and can hurt.
10. **Keep text out of the video.** Readable text in video is unreliable, so add titles and
    captions in the edit. In images, text works if specified carefully (see "Text in images").

## Saying what you don't want depends on the model

Two kinds of models behave differently, so check `model-notes.md` for the one you're using.

- **Video models, FLUX and Runway:** "no X" often *adds* X, because the model reads it as a mention.
  - Describe the positive state instead:
    - "no people" → "empty, deserted";
    - "no text" → "clean, unmarked surfaces";
    - "no camera movement" → "the camera holds completely still";
    - "doesn't talk" → "lips closed, breathing quietly".
  - Ask yourself what fills the space, and describe that.
- **GPT Image and Nano Banana:** these understand language better. Use the positive form first,
  then add **one short "Do not…" backstop** if needed, e.g. "Do not include any text or
  watermarks." Negating a *style* ("don't make it an illustration") doesn't work. Use concrete
  photographic cues instead.
- **Negative-prompt fields** (Kling, Wan, Qwen, Recraft V2/V3) take bare nouns as a comma list,
  without the word "no": "morphing, warping, extra fingers, text, watermark". Only use them
  where the model has one, through the item's `options`.
- **Order of fixes:** positive wording first, then a negative field, then a backstop sentence.

## Text-to-video brief (about 40–120 words)

```
[Shot size + angle], [one camera move: speed, start → end framing].
[CHARACTER BLOCK, pasted word for word]. [One visible action, with a tempo word: slow/steady/quick; real-time].
[Setting: place, time, weather, foreground and background].
[Light: source, direction, colour temperature]. [Style, medium, film stock or texture].
Audio. Ambience: … SFX: … [Speaker described by appearance], [voice description], says: [≤ 15–20 words per 8 s]. Music: … / No music.
```

## Image-to-video brief (about 15–40 words)

Once a start frame is given, **write only what changes**. Never re-describe the picture; it
"confuses the model", per Google. Refer to people generically ("the woman", "he").

```
[Subject] [action with speed + end state]. [Environmental motion: hair, dust, water, light].
[One camera move with speed and end framing] OR "The camera holds completely still."
[What stays still or unchanged, if it matters]. Audio. …
```

Also:
- Atmospheric motion (rain, smoke, flickering neon, drifting dust) is the cheapest way to make a
  shot feel alive with little risk.
- Don't ask a still to do something its framing doesn't allow. A head-and-shoulders portrait
  can't "stand up and walk away".

## First and last frames

- **Make the end frame by editing the start frame** ("change only the light to dusk"). Anything
  that differs between the two stills becomes motion, including unwanted drift.
- Put the "before" state in the first frame, then describe the transition and the order of
  events in the prompt, not the frames themselves.
- Both frames must have the same aspect ratio. Using the same image twice makes a loop.
- One practitioner test found Kling 3.0 matched both frames best, Seedance 2.5 second and
  MiniMax H3 third.

## Making still frames for video

The keyframe matters more than the prompt wording. Flaws in it get worse once animated.
- Generate the still at the **final aspect ratio**, at high resolution. Don't crop later.
- Choose a pose that implies the next motion, e.g. mid-gesture.
- Frame slightly wider than the final shot if a push-in is planned.
- State the light direction and colour temperature.
- Avoid small or half-hidden hands, which distort badly.
- For vertical video, centre the subject and prefer medium or close shots. Leave about 10% at
  the top and 15–20% at the bottom clear for the platform's interface.
- Show the subject and its motion immediately. A video "lives or dies in the opening shot".

## Characters and consistency

1. **Character block.** Write one fixed description: a name, age, face, hair, outfit and
   voice. Paste it **word for word** into every prompt. Even small wording changes break
   consistency.
2. **Reference sheet first.** Make a character sheet before any shot: front, side and back on
   plain grey, plus an expression close-up. Nano Banana Pro handles grids up to about 4×4.
3. **Re-anchor to the original reference**, not the last output. Repeated edits drift.
4. **Every prompt stands alone.** Models remember nothing between shots, so re-describe the
   setting, character and tone each time.
5. Seeds are not a consistency tool. At best they repeat identical inputs.

## Reference images

- **Give every reference a role, in that model's token format** (see model-notes). Example:
  "Image 1 is the scene; image 2 supplies the woman, appearance only; image 3 supplies the
  colour palette only."
- Lock roles when several people appear: "each character's look is locked to their own
  reference image, with no mixing of clothing or hair colour."
- Use fewer, cleaner references. One clean portrait beats five similar angles. Stability falls
  as the count rises.
- Order matters. On FLUX, the output follows image 1's aspect ratio; on Qwen, it follows the last image's.

## Image edits

```
[Verb] the [uniquely identified target: position, colour, size] from [A] to [B].
Keep [face and identity], [pose], [framing and camera angle], [lighting], [named background items], [label text "…"] exactly unchanged.
```

- Name each thing to keep. "Everything else" alone is weaker. Keep that list short and put it
  **after** the edit.
- Make **one change per round**, and restate the keep-list every round.
- For pixel-exact regions, composite the approved edit into the original afterwards.
- On Nano Banana, use Google's form: "Using the provided image, change only the [element] to [new
  element]. Keep everything else in the image exactly the same, preserving the original
  style, lighting, and composition."

## Text in images

- Put the exact words in "quotes".
- Say where the text goes, the font style (or a described typeface), its colour, and that it
  appears **once**.
- Spell unusual names letter by letter.
- On GPT Image, add "no extra text" and use quality `high` for small lettering.
- Best models for text: Nano Banana Pro, GPT Image 2.x and Recraft (designed typography). Use
  Qwen for Chinese text.
- A duplicated or misspelled word usually needs a fresh generation, not an edit.

## Realistic photos

- Describe a real camera capture: the device or lens, the angle and the light direction. Add one
  or two natural imperfections, like visible pores or flyaway hair.
- OpenAI's own example: "a candid, unretouched 35mm-style photo".
- For a phone or UGC look on Veo: "A selfie video of…, arm visible, slightly grainy, looks very
  film-like".

## Several shots in one clip (only on models that support it)

```
Overall: [theme, mood, pacing; the character block, identical across shots].
Shot 1 [0–3 s]: [shot size], [camera move]. [action]. [audio].
Hard cut.
Shot 2 [3–6 s]: …
Style: [global style last].
```

Convert this to each model's own syntax with model-notes (Kling `[Shot 1: …]`, Wan `Shot 1 [0–3 s]`,
FLUX `SHOT ONE: … HARD CUT.`, Seedance 2.0 "Shot 1 … cut to", Veo `[00:00-00:02]`). The default is
still **one moment per clip**. Use multi-shot only on purpose. For clips longer than the model
allows, chain clips: the last frame of one becomes the first frame of the next, and the
character and scene are restated each time.

## Worked example: the sailboat test, done properly

*Image (FLUX, so positive wording only):* "Cinematic wide shot, 35mm lens at eye level just above
the waterline. One small wooden sailboat with honey-varnished planks and a single cream canvas
sail floats alone in the centre of the lower half of the frame on a calm turquoise sea, an empty
deck and a clean, unmarked hull. Gentle ripples, soft reflection under the hull. Open sea to a
flat horizon on the upper third, peach-and-gold sky at golden hour, low sun behind camera left
giving warm rim light on the sail. Photoreal, natural colours, fine film grain."

*Video from that image (motion only):* "The boat rocks gently on slow swells and the sail ripples in
a light breeze; sunlight glitters on the water. Slow, steady push-in toward the boat, ending on a
medium shot. Audio. Ambience: soft lapping water, light wind. No music."
