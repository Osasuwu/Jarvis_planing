from dataclasses import dataclass


@dataclass
class HumanStakeholderProxy:
    role: str = "human_stakeholder"

    def respond(self, prompt: str) -> str:
        print(f"\n[Facilitator -> Human] {prompt}")
        print("Type your response (or '/interrupt' to stop):")
        value = input("> ").strip()
        if value.lower() == "/interrupt":
            raise KeyboardInterrupt("Human interrupted the meeting.")
        return value
