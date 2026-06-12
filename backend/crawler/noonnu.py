import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

BASE_URL = "https://noonnu.cc"

# html -> BeautifulSoup 객체를 반환
def get_noonnu_html(url: str):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    return soup

# scrape font
def scrape_font_detail(url: str):
    soup = get_noonnu_html(url)

     # name
    h2 = soup.find("h2")

    # category(형태) - sibling으로 찾기
    label = soup.find("span", string="형태")
    category_span = label.find_next_sibling("span")

    # tag
    h2 = soup.find("h2")
    tags = []

    for div in h2.find_next_siblings("div"):
        links = div.find_all("a")

        if links:
            tags = [a.text.strip() for a in links]
            break

    # download_url
    download_url = soup.find("a", class_="noon-yellow-button")



    # weights(검색 및 필터용) / webfonts
    webfont_pre = soup.find("pre", attrs={"name": "webfontSource"})

    weights = []
    webfonts = []

    if webfont_pre:
        text = webfont_pre.text

        weights = re.findall(r"font-weight:\s*(\d+)", text)
        weights = [int(w) for w in weights]

        urls = re.findall(r"url\(['\"]?([^'\")]+)", text)

        for weight, url in zip(weights, urls):
            webfonts.append({"weight": weight, "url": url})

    # license
    license_article = soup.find("article")

    # license_summary
    rows = soup.find_all("tr")
    license_summary = []
    for row in rows[1:]:  # 첫 줄 헤더 제외
        cells = row.find_all("td")
        values = [cell.get_text(" ", strip=True) for cell in cells]

        if len(values) >= 3:
            license_summary.append({
                "category": values[0],
                "scope": values[1],
                "allowed": values[2],
            })


    font_data = {
        "name": h2.text.strip(),
        "source": "noonnu",
        "is_paid": False,
        "license": license_article.get_text(" ", strip=True),
        "category": category_span.text.strip(),
        "tags": tags,
        "description": None,
        "weights": weights,
        "webfonts": webfonts,
        "download_url": download_url["href"],
        "source_url": url,
        "license_summary": license_summary,
    }

    return font_data


def scrape_font_urls(list_url: str):
    soup = get_noonnu_html(list_url)

    detail_urls = []

    for a in soup.find_all("a"):
        href = a.get("href")
        # 상대 경로를 절대경로로 변환 /font_page/694
        if href and "/font_page/" in href:
            full_url = urljoin(BASE_URL, href)
            detail_urls.append(full_url)

        # 중복 제거
    detail_urls = list(dict.fromkeys(detail_urls))

    return detail_urls