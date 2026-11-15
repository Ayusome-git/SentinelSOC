import asyncio
from app.scripts.seed_demo_scenario import run_scenario

if __name__ == "__main__":
    print("Executing safe demo reset...")
    asyncio.run(run_scenario(reset=True))
