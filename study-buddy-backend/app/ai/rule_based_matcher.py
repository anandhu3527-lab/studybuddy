def calculate_match_score(user: dict, candidate: dict) -> int:
    score = 0

    # Subject match (40)
    if set(user["subjects"]) & set(candidate["subjects"]):
        score += 40

    # Study time match (30)
    if user["study_time"] == candidate["study_time"]:
        score += 30

    # Same year (20)
    if user["year"] == candidate["year"]:
        score += 20

    # Same study mode (10)
    if user["study_mode"] == candidate["study_mode"]:
       score += 10

    #same course
    if user["course"]==candidate["course"]:
        score+20
    

    percentage =(score/120)*100
    return round(percentage)
