import requests
from bs4 import BeautifulSoup
import re

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
    siblings = h2.find_next_siblings("div")
    tag_div = siblings[1]
    tags = [a.text.strip() for a in tag_div.find_all("a")]

    # download_url
    download_url = soup.find("a", class_="noon-yellow-button")


    # weights (검색 및 필터용)
    weights_pre = soup.find("pre", attrs={"name": "webfontSource"})
    text = weights_pre.text
    # re.findall : 빈 list 생성 후 반복문 돌려서 list에 append까지 해줌
    weights = re.findall(r"font-weight:\s*(\d+)", text)
    # 문자열에서 숫자로 변경
    weights = [int(w) for w in weights]

    # webfonts (폰트 파일 적용 (굵기, url))
    webfont_pre = soup.find(
        "pre",
        attrs={"name": "webfontSource"}
    )

    text = webfont_pre.text

    urls = re.findall(
        r"url\(['\"]?([^'\")]+)",
        text
    )

    webfonts = []
    for weight, url in zip(weights, urls):
        webfonts.append({
            "weight": weight,
            "url": url
        })

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