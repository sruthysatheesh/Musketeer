from playwright.sync_api import sync_playwright

def fetch_latest_tweets_no_pinned(username, limit=10):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Open Twitter profile
        page.goto(f"https://twitter.com/{username}", timeout=60000)

        # Wait until tweets load
        page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)

        # Grab all tweet articles (including pinned)
        tweet_articles = page.query_selector_all('article[data-testid="tweet"]')

        tweets_cleaned = []
        for article in tweet_articles:
            # Skip pinned tweets
            if article.query_selector('svg[aria-label="Pinned Tweet"]'):
                continue

            # Extract tweet text
            tweet_text_divs = article.query_selector_all('div[data-testid="tweetText"]')
            text_parts = [div.inner_text().strip() for div in tweet_text_divs]
            full_text = " ".join(text_parts)

            # Extract timestamp
            time_tag = article.query_selector('time')
            timestamp = time_tag.get_attribute("datetime") if time_tag else None

            # Extract tweet link
            link_tag = article.query_selector('a[role="link"][href*="/status/"]')
            tweet_link = f"https://twitter.com{link_tag.get_attribute('href')}" if link_tag else None

            tweets_cleaned.append({
                "text": full_text,
                "timestamp": timestamp,
                "link": tweet_link
            })

            if len(tweets_cleaned) >= limit:
                break

        browser.close()
        return tweets_cleaned


if __name__ == "__main__":
    username = "elonmusk"
    tweets = fetch_latest_tweets_no_pinned(username, limit=5)
    for t in tweets:
        print(f"[{t['timestamp']}] {t['text']}\nLink: {t['link']}\n")
