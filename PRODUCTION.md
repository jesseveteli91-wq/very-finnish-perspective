# Very Finnish Perspective

Create one full YouTube episode and two vertical shorts per episode. Publish the same two shorts to TikTok; never publish the full episode there. Every short must include spoken and visible text, plus description: "Full-length videos exclusively on YouTube — Very Finnish Perspective."

## Narration

Configured repository secrets: ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID. Never put secret values in files or logs. Use this channel's configured voice, not another channel's voice.

Commit a new narration text file directly under scripts/episodes/ on main to generate it. A push runs only added/modified text files in the most recent commit. For multiple scripts, commit them together or separately (one generation per changed script). Alternatively run the ElevenLabs narration workflow manually with a script path. Do not modify a completed narration script casually: edits trigger paid regeneration. Check previous runs before retrying.

Output artifact: finnish-voiceover-RUN_ID, containing each script's narration.mp3, individual MP3 segments, character alignment JSON, source segment text and manifest with segment durations. Offset each segment's alignment by the cumulative actual audio durations when building subtitles. Artifacts expire after 30 days; archive production assets before expiry.

The generator splits long scripts into requests and uses previous/next text for continuity. No automatic retries after an ambiguous API failure. Review ElevenLabs generation history and any saved partial artifacts first. Use existing quota only; do not purchase credits or subscriptions automatically.

voice-test.txt is a technical test, never an episode or publication.

This repository currently generates narration only. Video rendering, visual/audio review, thumbnails, metadata and verified scheduling are separate production steps. A successful narration workflow is not evidence of a published video.
