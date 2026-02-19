from dataclasses import dataclass

from interaction.channel import InteractionChannel


@dataclass
class HumanStakeholderProxy:
    channel: InteractionChannel
    role: str = "human_stakeholder"

    def respond(self, prompt: str) -> str:
        self.channel.display(f"\n[Facilitator -> Human] {prompt}")
        return self.channel.prompt_text(
            "Type your response (or '/interrupt' to stop): ",
            allow_interrupt=True,
        )
