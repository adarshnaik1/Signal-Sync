import requests
import re


API_KEY = "pub_44655aa9ec2a4c808bd2b012040cb7ad"


def clean_summary(text):

    if not text:
        return ""

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove hashtags
    text = re.sub(r"#\S+", "", text)

    # Remove excessive spaces/newlines
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_valid_article(headline, summary):

    bad_keywords = [
        "youtube",
        "watch live",
        "whatsapp",
        "telegram",
        "subscribe",
        "otv",
        "video",
        "breaking news"
    ]

    combined = (headline + " " + summary).lower()

    # Reject noisy/promotional articles
    for word in bad_keywords:
        if word in combined:
            return False

    # Reject heavily non-English articles
    english_chars = sum(c.isascii() for c in combined)

    if len(combined) > 0:

        english_ratio = english_chars / len(combined)

        if english_ratio < 0.7:
            return False

    return True


def fetch_company_news(company_name):

    url = (
        f"https://newsdata.io/api/1/news?"
        f"apikey={API_KEY}"
        f"&q={company_name} stock"
        f"&language=en"
        f"&country=in"
        f"&category=business"
    )

    try:

        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("Failed to fetch news data.")

        data = response.json()

        articles = data.get("results", [])

        normalized_news = []

        company_keyword = company_name.split()[0].lower()

        # Strict filtering
        for article in articles:

            headline = article.get("title", "") or ""
            summary = article.get("description", "") or ""

            combined_text = (headline + " " + summary).lower()

            # Company relevance check
            if company_keyword not in combined_text:
                continue

            # Article quality check
            if not is_valid_article(headline, summary):
                continue

            normalized_news.append({

                "headline": headline,

                "summary": clean_summary(summary),

                "source": article.get("source_id"),

                "published_at": article.get("pubDate"),

                "url": article.get("link")

            })

        # Fallback → broader business news
        if len(normalized_news) == 0:

            for article in articles[:5]:

                headline = article.get("title", "") or ""
                summary = article.get("description", "") or ""

                if not is_valid_article(headline, summary):
                    continue

                normalized_news.append({

                    "headline": headline,

                    "summary": clean_summary(summary),

                    "source": article.get("source_id"),

                    "published_at": article.get("pubDate"),

                    "url": article.get("link")

                })

        return normalized_news[:5]

    except Exception as e:

        print(f"News Fetch Error: {e}")

        return []