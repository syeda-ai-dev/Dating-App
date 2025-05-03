import requests
from typing import Dict, List, Any
import openai
from openai import OpenAI
from datetime import datetime
import os
import logging
import time
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMMatchMaking:
    def __init__(self, config):
        # Base URL for user data
        self.base_url = config.DB_BASE_URL
        
        # OpenAI setup
        self.api_key = config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Create OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Add caching to reduce API calls
        self.score_cache = {}
        self.description_cache = {}
    
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}{user_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def generate_match_description(self, my_data: Dict[str, Any], other_user: Dict[str, Any]) -> str:
        """
        Use LLM to generate a personalized match description
        
        Args:
            my_data: Current user's data
            other_user: Other user's data
            
        Returns:
            Personalized match description
        """
        # Check cache first
        cache_key = f"{my_data.get('id')}:{other_user.get('id')}"
        if cache_key in self.description_cache:
            return self.description_cache[cache_key]
            
        # Not needed anymore since we remove this from response
        # We'll return a placeholder instead of making an API call
        description = f"Match between {my_data.get('name', 'User')} and {other_user.get('name', 'Match')}"
        
        # Store in cache
        self.description_cache[cache_key] = description
        return description
    
    def calculate_llm_match_score(self, my_data: Dict[str, Any], other_user: Dict[str, Any], strict: bool = True) -> float:
        """
        Use LLM to calculate a more nuanced match score between users
        
        Args:
            my_data: Current user's data
            other_user: Other user's data
            strict: If True, enforce strict compatibility rules
            
        Returns:
            Match score between 0 and 100
        """
        # Check if users are compatible based on gender preferences first
        if not self.is_compatible(my_data, other_user, strict):
            return 0
            
        # Calculate gender preference match bonus
        gender_preference_bonus = 0
        my_interest = my_data.get("interestedIn")
        other_gender = other_user.get("gender")
        
        if my_interest == "GIRLS" and other_gender == "FEMALE":
            gender_preference_bonus = 200  # Strong bonus for exact match
        elif my_interest == "BOYS" and other_gender == "MALE":
            gender_preference_bonus = 200  # Strong bonus for exact match
        elif my_interest == "BOTH":
            gender_preference_bonus = 50   # Smaller bonus for those who are open to both
        
        # For now, return just the gender bonus as base score since we're not using
        # the traditional algorithm anymore
        score = gender_preference_bonus
        
        logger.info(f"Match score for {other_user.get('name')} (gender: {other_gender}): {score}")
        
        return score
    
    def is_compatible(self, my_data: Dict[str, Any], other_user: Dict[str, Any], strict: bool = True) -> bool:
        """Basic compatibility check based on gender preferences"""
        gender1 = my_data.get("gender")
        gender2 = other_user.get("gender")
        interest1 = my_data.get("interestedIn")
        interest2 = other_user.get("interestedIn")
        
        if not all([gender1, gender2, interest1, interest2]):
            return not strict
            
        compatible1 = (
            (interest1 == "BOTH") or 
            (interest1 == "BOYS" and gender2 == "MALE") or
            (interest1 == "GIRLS" and gender2 == "FEMALE")
        )
        compatible2 = (
            (interest2 == "BOTH") or 
            (interest2 == "BOYS" and gender1 == "MALE") or
            (interest2 == "GIRLS" and gender1 == "FEMALE")
        )
        return compatible1 and compatible2 if strict else compatible1 or compatible2
    
    def get_matches(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get LLM-enhanced matches for a user
        
        Args:
            user_id: ID of the user to get matches for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of matched user data with LLM-enhanced scores and descriptions
        """
        start_time = time.time()
        logger.info(f"Starting match-making process for user {user_id}")
        
        # Get user data
        data = self.get_user_data(user_id)
        
        if not data.get("success"):
            raise Exception("Failed to get user data")
            
        # Extract my data and all users
        my_data = data.get("data", {}).get("myData", {})
        all_users = data.get("data", {}).get("usersData", [])
        
        logger.info(f"Found {len(all_users)} total users in database")
        logger.info(f"My gender preference: {my_data.get('interestedIn')}")
        
        # First try with strict matching to get exact gender preference matches
        strict_matches = self._find_matches(user_id, my_data, all_users, strict=True)
        logger.info(f"Found {len(strict_matches)} strict matches")
        
        # If we need more matches, try looser criteria
        matches = strict_matches
        if len(strict_matches) < limit:
            logger.info(f"Finding more matches with looser criteria")
            # Only get enough additional matches to reach the limit
            looser_matches = self._find_matches(user_id, my_data, all_users, strict=False)
            
            # Filter out duplicates
            existing_ids = {match.get("id") for match in matches}
            additional_matches = [m for m in looser_matches if m.get("id") not in existing_ids]
            
            # Add only as many as needed to reach the limit
            matches.extend(additional_matches[:limit - len(matches)])
            logger.info(f"Added {min(limit - len(strict_matches), len(additional_matches))} additional matches")
            
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x.get("matchScore", 0), reverse=True)
        
        # Trim to limit
        result = matches[:min(limit, len(matches))]
        
        # Log performance
        end_time = time.time()
        logger.info(f"Match-making completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Returning {len(result)} matches")
        
        return result
    
    def _find_matches(self, user_id: str, my_data: Dict[str, Any], all_users: List[Dict[str, Any]], strict: bool = True) -> List[Dict[str, Any]]:
        """
        Internal helper to find matches with given strictness level using LLM
        """
        matches = []
        skipped_count = 0
        processed_count = 0
        max_to_process = 50  # Limit processing to improve performance
        
        # First filter to prioritize matches based on gender preference
        filtered_users = []
        my_interest = my_data.get("interestedIn")
        
        # Prioritize users based on gender preference
        if my_interest == "GIRLS":
            # Put females first in the list
            females = [u for u in all_users if u.get("gender") == "FEMALE" and u.get("id") != user_id]
            others = [u for u in all_users if u.get("gender") != "FEMALE" and u.get("id") != user_id]
            filtered_users = females + others
        elif my_interest == "BOYS":
            # Put males first in the list
            males = [u for u in all_users if u.get("gender") == "MALE" and u.get("id") != user_id]
            others = [u for u in all_users if u.get("gender") != "MALE" and u.get("id") != user_id]
            filtered_users = males + others
        else:
            # No specific preference, process all
            filtered_users = [u for u in all_users if u.get("id") != user_id]
        
        for user in filtered_users:
            if processed_count >= max_to_process:
                logger.info(f"Reached processing limit of {max_to_process} users")
                break
                
            processed_count += 1
            
            # Calculate match score using LLM
            score = self.calculate_llm_match_score(my_data, user, strict=strict)
            
            if score > 0:
                user_with_score = user.copy()
                user_with_score["matchScore"] = score
                user_with_score["matchDescription"] = self.generate_match_description(my_data, user)
                matches.append(user_with_score)
            else:
                skipped_count += 1
                
        logger.info(f"Processed {processed_count} users, skipped {skipped_count} due to incompatibility or low scores")
        return matches
