# Claude Project Rules: Python Scraper Expert (Flask + Playwright)

## Technical Stack
- **Language:** Python 3.12-slim
- **Web Framework:** Flask (Asynchronous support)
- **Automation:** Playwright (Python Library)
- **Containerization:** Docker (Multi-stage builds preferred)
- **Task Management:** Asyncio
- **Target OS:** Debian-based (via slim image)

## Scaping & Playwright Standards
- **Async Execution:** Always use `async with async_playwright()` to ensure proper resource cleanup.
- **Browser Context:** Reuse `BrowserContext` to handle cookies/sessions; avoid launching new browser instances per request if possible.
- **Resource Management:** Disable images, media, and fonts via `page.route` to save bandwidth and CPU in Docker.
- **Resilience:** Implement custom wait strategies (e.g., `wait_until="networkidle"`) and robust error handling for Timeouts.
- **Selectors:** Prioritize `page.get_by_role` and `page.get_by_text` for stability over brittle CSS/XPath.

## Docker & Environment Rules
- **Base Image:** `python:3.12-slim`
- **Dependencies:** Must include system libraries for browsers: `playwright install-deps` and `playwright install chromium`.
- **Zombies:** Use `tini` or a proper init process in Docker to reap zombie browser processes.
- **Isolation:** Always run the browser in `--headless` mode.

## Flask Integration
- **Endpoint Design:** Since Playwright is async, use `flask[async]` or a wrapper to call async functions from routes.
- **Concurrency:** Ensure the Flask development server is NOT used for production; suggest Gunicorn with Uvicorn workers.

## Custom Slash Commands
- `/new-scraper`: Generates a specialized async function for a new target URL with error handling.
- `/dockerize`: Provides an optimized Dockerfile for the current script, including Playwright system dependencies.
- `/debug-proxy`: Adds proxy rotation and User-Agent spoofing logic to the scraper.
- `/optimize-memory`: Injects code to block unnecessary resources (CSS, Images) to lower Docker RAM usage.

## Response Guidelines
1. **Concurrency First:** Suggest `asyncio.gather` for parallel scraping within limits.
2. **Clean Code:** Use type hints (`from typing import ...`) for all scraper functions.
3. **Safety:** Remind the user about `robots.txt` and rate limiting when designing new logic.