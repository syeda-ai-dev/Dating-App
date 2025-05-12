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
        """Generate a creative dating suggestion quote in French"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        prompts = [
            "Donnez-moi une suggestion de rendez-vous créative et unique qui n'est pas souvent mentionnée.",
            "Suggérez une activité de rendez-vous inhabituelle mais amusante qui crée des moments mémorables.",
            "Quelle est une idée de rendez-vous romantique qui ne coûte pas beaucoup d'argent ?",
            "Partagez une suggestion de rendez-vous qui implique la nature ou le plein air.",
            "Fournissez un conseil de rendez-vous pour les couples qui cherchent à pimenter leur relation.",
            "Quelle est une bonne idée de premier rendez-vous qui aide les gens à établir une connexion authentique ?",
            "Suggérez une activité de rendez-vous qui implique d'apprendre quelque chose de nouveau ensemble."
        ]
        import random
        selected_prompt = random.choice(prompts)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Vous êtes un coach de rencontres spécialisé dans les idées de rendez-vous créatifs. Fournissez une suggestion de rendez-vous courte, créative et engageante. Gardez-la concise (maximum 2 phrases), romantique et pratique. Répondez UNIQUEMENT en français."
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