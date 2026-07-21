class EvaluationDataset:
    """Placeholder representing standard ground truth reference queries for testing."""

    @staticmethod
    def get_ground_truth() -> dict:
        return {
            "The vehicle satisfies public risk safety rules": ["FAA-450.115"],
            "Reactor containment requirements must describe safety design": [
                "NRC-10CFR50"
            ],
        }
