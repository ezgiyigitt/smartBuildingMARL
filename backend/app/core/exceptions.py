class DatasetNotAvailableError(RuntimeError):
    """Raised when a registered dataset has not been downloaded."""


class ScenarioIncompatibleError(RuntimeError):
    """Raised when a CityLearn schema cannot support the research question."""
