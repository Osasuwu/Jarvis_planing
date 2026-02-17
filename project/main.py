from orchestration.waterfall_controller import WaterfallController


def main() -> None:
    controller = WaterfallController()
    controller.run()


if __name__ == "__main__":
    main()
