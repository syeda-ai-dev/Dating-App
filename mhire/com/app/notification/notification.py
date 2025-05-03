import os
from datetime import datetime
from typing import List
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from mhire.com.config.config import Config

class Quote(BaseModel):
    quote: str
    timestamp: str

class Notification:
    def __init__(self, config: Config):
        self.config = config
        self.api_key = self.config.OPENAI_API_KEY
        self.openai_endpoint = self.config.OPENAI_ENDPOINT
        self.model = self.config.MODEL
        if not all([self.api_key, self.openai_endpoint, self.model]):
            raise Exception("OPENAI_API_KEY, OPENAI_ENDPOINT, and MODEL are required")
        
        self.scheduler = AsyncIOScheduler()
        self.quotes_history: List[Quote] = []
        
        # Start the scheduler
        self.scheduler.add_job(
            self.store_daily_quote,
            CronTrigger(hour=9, minute=0),
            id="daily_quote"
        )
        self.scheduler.start()

    async def generate_quote(self):
        """Generate a creative dating suggestion quote"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        prompts = [
            "Give me a creative and unique dating suggestion that's not commonly mentioned.",
            "Suggest an unusual but fun dating activity that creates memorable moments.",
            "What's a romantic dating idea that doesn't cost much money?",
            "Share a dating suggestion that involves nature or outdoors.",
            "Provide a dating tip for couples looking to spice up their relationship.",
            "What's a good first date idea that helps people connect genuinely?",
            "Suggest a date activity that involves learning something new together."
        ]
        import random
        selected_prompt = random.choice(prompts)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a dating coach specializing in creative date ideas. Provide a short, creative, and engaging dating suggestion. Keep it concise (maximum 2 sentences), romantic, and practical."
                },
                {
                    "role": "user",
                    "content": selected_prompt
                }
            ],
            "max_tokens": 100,
            "temperature": 0.9,
            "presence_penalty": 0.6,
            "frequency_penalty": 0.6
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.openai_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            quote = data["choices"][0]["message"]["content"].strip()
            return quote

    async def store_daily_quote(self) -> Quote:
        """Store and return a new dating suggestion quote"""
        quote_text = await self.generate_quote()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        quote = Quote(quote=quote_text, timestamp=timestamp)
        self.quotes_history.append(quote)
        if len(self.quotes_history) > 30:
            self.quotes_history.pop(0)
        return quote

    def cleanup(self):
        """Cleanup resources"""
        if self.scheduler.running:
            self.scheduler.shutdown()
