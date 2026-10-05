"""Adversarial scenario runner. §8. TODO: implement."""

SCENARIOS = ["spoofed_reading", "frozen_sensor", "guardian_unreachable",
             "duplicate_event", "replayed_reading"]


def main() -> None:
    for name in SCENARIOS:
        print(f"[TODO] run scenario: {name}")


if __name__ == "__main__":
    main()
