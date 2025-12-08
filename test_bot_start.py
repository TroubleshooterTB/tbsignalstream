#!/usr/bin/env python3
"""Quick test to verify /start endpoint accessibility"""

import requests

TRADING_BOT_SERVICE_URL = "https://trading-bot-service-vmxfbt7qiq-el.a.run.app"

# Test without auth (should fail with 401)
print("Testing /start endpoint without auth...")
response = requests.post(f"{TRADING_BOT_SERVICE_URL}/start", 
                         json={"symbols": ["RELIANCE-EQ"], "mode": "paper", "strategy": "pattern"})
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
print()

# Test /health endpoint
print("Testing /health endpoint...")
response = requests.get(f"{TRADING_BOT_SERVICE_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test /status endpoint without auth
print("Testing /status endpoint without auth...")
response = requests.get(f"{TRADING_BOT_SERVICE_URL}/status")
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
