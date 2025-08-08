import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

def login_and_fetch_tweets(search_url, limit=5):
    username = os.getenv("TWITTER_USER")
    password = os.getenv("TWITTER_PASS")

    if not username or not password:
        raise ValueError("Please set TWITTER_USER and TWITTER_PASS environment variables.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Change to True when stable
        page = browser.new_page()

        print("[INFO] Opening Twitter login page...")
        page.goto("https://twitter.com/login", timeout=60000)

        # STEP 1: Enter username
        print("[INFO] Entering username...")
        page.locator('input[name="text"]').fill(username)
        page.wait_for_timeout(1000)  # Allow UI to update

        next_btn = page.locator('div[role="button"] >> text=/next/i')
        if next_btn.is_visible():
            next_btn.click()
            print("[INFO] Clicked 'Next'")
        else:
            print("[WARN] 'Next' button not found — pressing Enter")
            page.keyboard.press("Enter")
        page.wait_for_timeout(2000)

        # STEP 2: Optional phone/email verification
        if page.locator('input[name="text"]').is_visible():
            print("[INFO] Verification step detected...")
            page.locator('input[name="text"]').fill(username)
            page.wait_for_timeout(1000)
            verify_btn = page.locator('div[role="button"] >> text=/next/i')
            if verify_btn.is_visible():
                verify_btn.click()
                print("[INFO] Clicked verification 'Next'")
            else:
                print("[WARN] Verification button not found — pressing Enter")
                page.keyboard.press("Enter")
            page.wait_for_timeout(2000)

        # STEP 3: Enter password
        print("[INFO] Entering password...")
        page.locator('input[name="password"]').fill(password)
        page.wait_for_timeout(500)
        login_btn = page.locator('div[role="button"] >> text=/log in/i')
        if login_btn.is_visible():
            login_btn.click()
            print("[INFO] Clicked 'Log in'")
        else:
            print("[WARN] 'Log in' button not found — pressing Enter")
            page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        # STEP 4: Navigate to search URL
        print("[INFO] Navigating to search page...")
        page.goto(search_url, timeout=60000, wait_until="networkidle")

        # STEP 5: Wait for tweets to load
        page.wait_for_selector('article[data-testid="tweet"]', timeout=30000)

        # STEP 6: Extract tweets
        tweets = []
        for article in page.locator('article[data-testid="tweet"]').all():
            if article.locator('svg[aria-label="Pinned Tweet"]').count() > 0:
                continue

            text_parts = [div.inner_text().strip()
                          for div in article.locator('div[data-testid="tweetText"]').all()]
            full_text = " ".join(text_parts)

            timestamp = None
            if article.locator('time').count() > 0:
                timestamp = article.locator('time').get_attribute("datetime")

            link = None
            if article.locator('a[role="link"][href*="/status/"]').count() > 0:
                link = "https://twitter.com" + article.locator(
                    'a[role="link"][href*="/status/"]').first.get_attribute('href')

            tweets.append({
                "text": full_text,
                "timestamp": timestamp,
                "link": link
            })

            if len(tweets) >= limit:
                break

        browser.close()
        return tweets


if __name__ == "__main__":
    SEARCH_URL = "https://twitter.com/search?q=from%3Aelonmusk&src=typed_query&f=live"
    results = login_and_fetch_tweets(SEARCH_URL, limit=5)
    for t in results:
        print(f"[{t['timestamp']}] {t['text']}\nLink: {t['link']}\n")
