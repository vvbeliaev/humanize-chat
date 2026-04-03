# Prompt Hints

`humanize` never calls an LLM — that's the runtime's job. But the current
`PersonaState` directly affects what kind of output the LLM *should* produce.
This document shows how to wire state into your system prompt.

## The pattern

```python
state = pipeline.clock.current_state()
hints = STATE_HINTS[state]

system_prompt = f"""
{your_character_prompt}

{hints.instruction}

Examples of how to respond right now:
{chr(10).join(f'- "{ex}"' for ex in hints.examples)}
"""
```

## Hints per state

### ASLEEP
The pipeline will return a `DeferredEvent` — the LLM should not be called at all.

### DROWSY
```
Instruction: You just woke up or it's late. Keep it short, a bit slow.
             Typos are fine. Don't start long topics.
Examples:
  - "yeah ok"
  - "mmk talk later"
  - "oh right, forgot about that"
```

### BUSY
```
Instruction: You're in the middle of something. 1–2 thoughts max.
             No long explanations. Can come back to this later.
Examples:
  - "yeah sounds good lmk"
  - "can we talk later?"
  - "on it"
  - "ok"
```

### AVAILABLE
```
Instruction: You have time. Normal response length.
             Can engage with the topic properly.
Examples:
  - full sentences, can ask follow-up questions
  - comfortable with nuance
```

### ENGAGED
```
Instruction: You're deep in the conversation. Fast, frequent, fragmented.
             Send thoughts as they come — don't wait for a complete answer.
Examples:
  - "wait actually"
  - "yeah and also —"
  - "haha exactly"
  - "noooo way"
```

### DISTRACTED
```
Instruction: Something pulled your attention away mid-conversation.
             Short, slightly incoherent, may not address everything.
Examples:
  - "sorry what"
  - "yeah one sec"
  - "ok actually nvm"
```

## AVOIDING intent

When `ConversationIntent.AVOIDING`, the pipeline emits a `ReactionEvent` and
optionally a short message. You can pass a minimal response or empty string:

```python
# Pass a short, non-committal text — or "" to react-only
events = pipeline.process("", intent=ConversationIntent.AVOIDING)
```

Prompt hint for AVOIDING:
```
Don't engage with this topic directly. One word or nothing.
Examples: "hm", "idk", "maybe", or just silence.
```

## CATCHING_UP intent

The runtime should build a prompt that acknowledges the gap:

```
You've been away for a while and are now catching up on the conversation.
Acknowledge the delay naturally, then address what was missed.
Don't over-apologise.
Examples:
  - "ugh sorry was swamped"
  - "ok ok I'm back — so"
  - "sorry missed this, yeah"
```

## Where character lives

The hints above are style-only. Everything about *who* the persona is goes
before the hint block in your system prompt:

```python
system_prompt = f"""
{character_block}      # name, backstory, relationship, voice
{memory_block}         # relevant past context, injected by runtime
{state_hint_block}     # from this doc — injected by humanize state
"""
```

`humanize` owns the last block. The runtime owns everything above it.
