from ai.rule_based_matcher import calculate_match_score
from bson import ObjectId
from core.security import encode_response

async def find_best_matches(user_profile: dict, profiles_collection):
    matches = []

    query = {
        "_id": {"$ne": ObjectId(user_profile["_id"])},
        "interested_field": user_profile["interested_field"]
    }

    cursor = profiles_collection.find(query)

    async for candidate in cursor:
        percentage = calculate_match_score(user_profile, candidate)
        feedscore = candidate.get("feedscore", 0)

        if percentage > 0:
            matches.append({
                "profile_id": encode_response(str(candidate["_id"])),
                "name": candidate["name"],
                "subjects": candidate.get("subjects", []),
                "percentage": percentage,
                "feedscore": feedscore
            })

    # Sort by percentage (desc), then feedscore (desc)
    matches.sort(
        key=lambda x: (x["percentage"], x["feedscore"]),
        reverse=True
    )

    return matches
