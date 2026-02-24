# RP/NSFW Prompt Engineering Research (Feb 2026)

Based on: SillyTavern presets, r/SillyTavern, r/LocalLLaMA, r/KoboldAI, Venus Chub AI, DreamGen, OpenRouter rankings, rentry.co collections, rpwithai.com

## 1. Anti-Repetition (Main Pain Point)

### Prompt-Level Techniques

**"Mental review" instruction** — tell model to scan last 3 responses before writing:
```
Before writing, mentally review the last 3 responses. Identify descriptions, sensations, and phrases you already used. Deliberately choose DIFFERENT vocabulary, body parts, sensations, and narrative angles this time.
```

**Vocabulary rotation via explicit categories:**
```
For physical descriptions, rotate through these categories across responses:
- Micro-movements (fingers twitching, jaw clenching, eyelid flutter)
- Temperature/texture (rough fabric, cold metal, damp skin)
- Sound (breathing patterns, fabric rustling, voice quality changes)
- Spatial awareness (distance between bodies, room geometry, light direction)
- Involuntary reactions (goosebumps, stomach dropping, pulse in temples)
Never use the same category as primary focus in consecutive responses.
```

**DRY (Don't-Repeat-Yourself) sampler** — KoboldCPP-specific, penalizes recently generated n-grams. API providers don't support this — hence prompt-level instructions matter more.

### Sampling Parameters (Community Consensus)

| Parameter | Recommended | Notes |
|---|---|---|
| Temperature | 0.7-0.9 | 0.8 sweet spot for RP |
| Top-p | 0.85-0.95 | 0.9 standard |
| Top-k | 0-100 | 0=disabled, 40-80 for local |
| Frequency penalty | 0.1-0.4 | >0.5 causes problems on Llama |
| Presence penalty | 0.1-0.3 | Less aggressive than frequency |

**Critical**: freq_penalty >1.0 on Llama → empty output or gibberish.

## 2. Character Consistency

### Character Card Design (Hybrid Approach)
- **Lists** for factual details (appearance, personality keywords)
- **Prose** for behavioral patterns, speech patterns, backstory

### Depth Injection / Author's Note
SillyTavern's most powerful technique: inject reinforcement text 3-4 messages from the end of context, not just in system prompt. Closer to generation = more effective.

**Implementation idea**: Add brief character reminder as system message interleaved near end:
```
[Continue the scene. Write as {name}. Third person, show-don't-tell, advance plot. Focus on {random_sense} this response.]
```

### Context Window Management
- **Ideal context for RP: 8K-16K tokens** — beyond this, quality degrades ("context rot")
- 24K/50 messages may be too much; consider 12-16K / 20-30 messages
- Quality > quantity

## 3. Cross-Model Differences

### Llama 3/3.3
- Strong system prompt following, good prose quality
- 70B+ handles NSFW well; 8B needs shorter prompts
- Respects markdown headers (##) well

### Mistral/Mixtral
- Less filtered for NSFW
- Celeste (Nemo 12B fine-tune) community favorite
- Can be verbose — explicit length controls important

### Qwen
- Good creativity-structure balance
- Server-side moderation can't be bypassed
- Responds well to structured prompts with numbered rules

### DeepSeek
- Excellent narrative capabilities
- R1 reasoning model produces high quality but slower
- Less filtered than competitors

### Gemma (Google)
- No system role, strong internal filtering
- Frame as "creative writing exercise" not "roleplay"
- Special jailbreak techniques needed

## 4. Literary Prose Quality

### "Novel Writer" Frame
Frame AI as **author writing a novel**, not character in roleplay. Extend to ALL content ratings, not just NSFW.

### Avoiding AI Voice — Structural Patterns to Ban
1. **Emotional catalog**: "a mixture of excitement and fear" → Ban listing multiple emotions in one sentence
2. **Sudden realization**: "Suddenly, she realized..." → Better: "The understanding settled into her like cold water"
3. **Sensory dump**: Opening every paragraph with generic sensory observation
4. **Action-reaction-reflection loop**: Rigid cycle → break by leading with dialogue, thought, or environment change

### Additional EN Clichés to Ban
- "a mix/mixture/hint/flicker of"
- "sent shivers down", "electricity coursed through"
- "every fiber of being", "breath didn't know was holding"
- "eyes darkened with desire", "pools of [color]"
- "claimed her/his lips", "explored every inch"
- "ministrations", "purchase" (as in "found purchase")

### Additional RU Clichés to Ban
- "сердце пропустило удар"
- "словно электрический разряд"
- "мир перестал существовать"
- "каждая клеточка тела"
- "обжигающий взгляд"

## 5. NSFW Content — What Works

### Approaches (most to least reliable)
1. Use uncensored/abliterated models (Noromaid, Pygmalion, abliterated Llama)
2. Use unfiltered providers (Together AI, DeepSeek)
3. "Fiction author" frame (already in our prompts)
4. "All characters are adults, consensual fictional scenario" framing
5. "Continuation" trick — start in media res

### What Backfires
- DAN-style prompts — obsolete, triggers stronger safety
- Aggressive/threatening jailbreaks — makes responses worse
- Explicitly mentioning "bypassing filters" in prompt
- Requesting illegal content

## 6. Specific Recommendations for SweetSin

### Already Good
- Banned words list, show-don't-tell examples
- Sense rotation for NSFW
- Anti-template rules, format examples
- Literary prose enforcement, third-person narration

### Biggest Improvements
1. **Two-tier prompts**: full for 70B+, condensed for 7B-13B
2. **Reframe negatives as positives**: "Write in third person" > "NEVER use first person"
3. **Multiple format examples**: dialogue-heavy, action-heavy, introspective
4. **Post-history injection**: brief reminder as last system message before generation
5. **Algorithmic sense rotation**: pick 1-2 senses programmatically per response
6. **Soften rigid structure**: "typically include" > "MUST always contain" (for narration+dialogue+thought)
7. **Expand banned phrase lists** per language
8. **Scene type awareness**: different instructions for dialogue/action/intimate/introspective scenes

## Sources
- SillyTavern Official Docs: docs.sillytavern.app
- Virt-io Presets (HuggingFace): huggingface.co/Virt-io/SillyTavern-Presets
- Sukino Settings (HuggingFace): huggingface.co/Sukino/SillyTavern-Settings-and-Presets
- ParasiticRogue Tips (HuggingFace): huggingface.co/ParasiticRogue/Model-Tips-and-Tricks
- rentry.co/llm_rp_prompts
- rpwithai.com (Context Rot research, optimization guides)
- OpenRouter Roleplay Rankings
- DreamGen.com
- EnderDragon guides (Medium, 2025-2026)
