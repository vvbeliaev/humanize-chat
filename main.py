"""Quick smoke test — runs the full pipeline with the PrintTransport."""

import asyncio
from datetime import datetime, timezone

from humanize_chat import (
    BaseAdapter,
    PersonaConfig,
    PersonaState,
    PrintTransport,
    ResponsePipeline,
)


async def demo(state: PersonaState, text: str) -> None:
    config = PersonaConfig.default()
    pipeline = ResponsePipeline(config)
    transport = PrintTransport()
    adapter = BaseAdapter(transport)

    print(f"\n--- state: {state.value} ---")
    events = list(pipeline.process(text, state=state))
    await adapter.deliver(events)


async def main() -> None:
    sample = (
        "Hey! Yeah I saw the PR. Looks good overall. "
        "One thing — the retry logic might be too aggressive for the prod environment. "
        "Can we cap it at 3 attempts?"
    )

    for state in [
        PersonaState.ENGAGED,
        PersonaState.BUSY,
        PersonaState.DROWSY,
        PersonaState.ASLEEP,
    ]:
        await demo(state, sample)


if __name__ == "__main__":
    asyncio.run(main())
