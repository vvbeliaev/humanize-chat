# humanize

**Communication behavior model for LLM runtimes.**

`humanize` sits between an LLM call and a messaging channel. It answers two questions:

- **When and how urgently** does the persona respond? → state machine
- **How sloppy and fragmented** are the messages? → delivery heuristics

It does not know who the persona is, what they remember, or what they say. That belongs to the runtime.

## Two layers

**Behavioral state machine** — models availability over time:

- Circadian schedule (sleep / drowsy / busy / available)
- Calendar overrides (standup → BUSY, etc.)
- Conversation activity (back-and-forth → ENGAGED)
- External triggers ("commuting" → DISTRACTED for 40 min)

**Delivery heuristics** — applies state to outgoing messages:

- Message splitting (sentence → chunk boundaries, capped by state)
- Keyboard-adjacent typos, casual punctuation
- Typing indicator duration, inter-chunk pauses, read delay

## What stays outside

Character, memory, voice, prompts — all runtime concerns. `humanize` exposes `StatePromptHints` so runtimes can shape LLM style to match the current state, but it never calls the LLM itself.

## Integration

```
incoming messages
    → MessageAccumulator      (batch rapid messages into one LLM call)
    → hints = clock.prompt_hints()          # use in your system prompt
    → response = your_llm(prompt, messages)
    → events = pipeline.process(response)   # humanize takes over
    → YourTransport.deliver(events)
```

`Transport` is an ABC — implement it for Telegram, nanobot, Discord, or anything else.
