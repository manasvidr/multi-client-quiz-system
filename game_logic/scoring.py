def check_answer(player_answer: str, correct_answer: str, acceptable: list = None) -> bool:
    norm_player = player_answer.strip().lower()
    norm_correct = correct_answer.strip().lower()

    if norm_player == norm_correct:
        return True

    if acceptable:
        for alt in acceptable:
            if norm_player == alt.strip().lower():
                return True

    return False


def update_score(scores: dict, username: str, correct: bool, time_remaining: float = 0) -> dict:
    if username not in scores:
        scores[username] = 0

    if correct:
        bonus = int(time_remaining)
        scores[username] += 10 + bonus

    return scores


def get_sorted_scores(scores: dict) -> list:
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)