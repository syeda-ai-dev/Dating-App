from fastapi import APIRouter
from typing import Dict, Any, List
from mhire.com.app.match_making.match_making import LLMMatchMaking
from mhire.com.config.config import Config

config = Config()
router = APIRouter(
    prefix="/match",
    tags=["match-making"],
    responses={404: {"description": "Not found"}},
)

match_making_service = LLMMatchMaking(config)

def clean_matches_for_response(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned_matches = []
    for match in matches:
        clean_match = match.copy()
        if 'matchScore' in clean_match:
            del clean_match['matchScore']
        cleaned_matches.append(clean_match)
    return cleaned_matches

@router.get("/recommendations/{user_id}")
async def get_match_recommendations(user_id: str):
    matches = match_making_service.get_matches(user_id, limit=5)
    cleaned_matches = clean_matches_for_response(matches)
    return {
        "success": True,
        "statusCode": 200,
        "message": "Match recommendations retrieved successfully",
        "data": {
            "matches": cleaned_matches,
            "count": len(cleaned_matches)
        }
    }
