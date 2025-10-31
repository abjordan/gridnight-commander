"""
Script to take a screenshot of GridNight Commander for README
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from textual.pilot import Pilot
from gridnight_commander.cli import GridFsBrowser

load_dotenv()

async def take_screenshot():
    """Run the app and take a screenshot"""

    # Connection details
    user = os.getenv("MONGO_ROOT_USER")
    passwd = os.getenv("MONGO_ROOT_PASSWORD")
    server = os.getenv("MONGO_SERVER")
    port = os.getenv("MONGO_PORT")
    connection_string = f"mongodb://{user}:{passwd}@{server}:{port}/"

    app = GridFsBrowser()

    async with app.run_test() as pilot:
        # Wait for app to initialize
        await pilot.pause(0.5)

        # Press 'c' to open connection dialog
        await pilot.press("c")
        await pilot.pause(0.3)

        # Fill in connection details
        # Focus connection string input (should be first input)
        await pilot.press("tab")  # Move to connection string
        # Clear and type connection string
        for _ in range(50):  # Clear existing text
            await pilot.press("backspace")
        for char in connection_string:
            await pilot.press(char)

        await pilot.pause(0.2)

        # Move to database name
        await pilot.press("tab")
        for _ in range(20):
            await pilot.press("backspace")
        for char in "gnc-test":
            await pilot.press(char)

        await pilot.pause(0.2)

        # Submit the form (press Connect button)
        await pilot.press("tab")  # Move to Connect button
        await pilot.press("enter")

        # Wait for connection and tree population
        await pilot.pause(2.0)

        # Expand Dune bucket (press enter on first tree node)
        await pilot.press("down")  # Move to first bucket
        await pilot.press("enter")  # Expand it
        await pilot.pause(0.5)

        # Select a file
        await pilot.press("down")  # Move to first file
        await pilot.pause(0.5)

        # Take screenshot
        screenshot_path = Path("docs/screenshot.svg")
        screenshot_path.parent.mkdir(exist_ok=True)

        print(f"Taking screenshot to {screenshot_path}...")
        pilot.app.save_screenshot(screenshot_path)

        print(f"✅ Screenshot saved to {screenshot_path}")

if __name__ == "__main__":
    asyncio.run(take_screenshot())
