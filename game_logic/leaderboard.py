from game_logic.scoring import get_sorted_scores


def generate_leaderboard(scores: dict) -> str:
    sorted_scores = get_sorted_scores(scores)
    score_str = ",".join(f"{name}:{pts}" for name, pts in sorted_scores)
    return f"SCORE|{score_str}"


def display_leaderboard(leaderboard_msg: str):
    if not leaderboard_msg.startswith("SCORE|"):
        print("[Leaderboard] Invalid format.")
        return

    _, data = leaderboard_msg.split("|", 1)
    entries = data.split(",")

    print("\n" + "=" * 35)
    print("        LEADERBOARD  ")
    print("=" * 35)
    for rank, entry in enumerate(entries, start=1):
        name, score = entry.split(":")
        medal = ["1st", "2nd", "3rd"][rank - 1] if rank <= 3 else f" {rank}."
        print(f"  {medal}  {name:<15} {score} pts")
    print("=" * 35 + "\n")
