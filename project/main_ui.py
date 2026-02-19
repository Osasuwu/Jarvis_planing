from interaction.channel import MinimalUIChannel
from orchestration.waterfall_controller import WaterfallController


def main() -> None:
    channel = MinimalUIChannel()
    controller = WaterfallController(channel=channel)
    controller.run()


if __name__ == "__main__":
    main()
