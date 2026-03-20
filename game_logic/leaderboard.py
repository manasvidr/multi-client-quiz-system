def generate_leaderboard(players):
    """
    Returns sorted list:
    [("Alice", {"score": 30}), ("Bob", {"score": 20})]
    """
    return sorted(players.items(), key=lambda x: x[1]["score"], reverse=True)


def format_leaderboard(leaderboard):
    """
    Converts leaderboard into protocol string
    Example:
    SCORE|Alice:30,Bob:20
    """
    return "SCORE|" + ",".join(
        [f"{player}:{data['score']}" for player, data in leaderboard]
    )
