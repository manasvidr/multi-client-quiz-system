def check_answers(correct_answer, answers):
    """
    answers format:
    {
        "Alice": ("Paris", 3.2),
        "Bob": ("London", 5.1)
    }
    """
    results = {}

    for player, (ans, time_taken) in answers.items():
        if ans.strip().lower() == correct_answer.strip().lower():
            results[player] = {"correct": True, "time": time_taken}
        else:
            results[player] = {"correct": False, "time": time_taken}

    return results


def update_scores(players, results):
    """
    players format:
    {
        "Alice": {"score": 0},
        "Bob": {"score": 0}
    }
    """
    for player, data in results.items():
        if data["correct"]:
            bonus = max(0, 10 - int(data["time"]))
            players[player]["score"] += 10 + bonus
        else:
            # optional negative marking
            players[player]["score"] -= 2
