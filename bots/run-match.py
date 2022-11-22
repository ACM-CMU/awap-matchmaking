import json
import team1
import team2

if __name__ == "__main__":
    team1_score = team1.main()
    print(f"Team 1 score = {team1_score}")
    team2_score = team2.main()
    print(f"Team 2 score = {team2_score}")

    assert team1_score > 0
    assert team2_score > 0

    outcome = 1 if team1_score > team2_score else 2
    score = {"scores": {"Team1": team1_score, "Team2": team2_score, "Outcome": outcome}}
    print(json.dumps(score))
