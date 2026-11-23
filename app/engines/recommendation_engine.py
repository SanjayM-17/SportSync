
def recommend_options(feasible_options):
    """
    Rank feasible facility options using best-fit capacity.

    Smaller unused capacity is preferred.
    This only orders recommendations.
    It does not automatically select or book resources.
    """

    if not feasible_options:
        return []

    recommended = sorted(
        feasible_options,
        key=lambda option: (
            option["facility"]["capacity"],
            option["facility"]["facility_name"]
        )
    )

    return recommended

