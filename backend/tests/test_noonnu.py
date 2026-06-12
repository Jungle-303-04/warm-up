from crawler.noonnu import scrape_font_detail, scrape_font_urls
from models.font import Font
from sqlmodel import Session,select
from database import engine


url = "https://noonnu.cc/font_page/694"

font_data = scrape_font_detail(url)
with Session(engine) as session:
    # 폰트 보유 여부 조회
    existing_font = session.exec(
        select(Font).where(
            Font.source_url == font_data["source_url"]
        )
    ).first()

    if existing_font:
        print("이미 저장된 폰트입니다.")
    
    else:
        font = Font(**font_data)

        session.add(font)
        session.commit()

        print("저장 완료")

# 폰트 목록 가져오기
list_url = "https://noonnu.cc/index"
urls = scrape_font_urls(list_url)

with Session(engine) as session:
    # 상세페이지 크롤링
    for url in urls:
        try:
            font_data = scrape_font_detail(url)
        except Exception as e:
            print("크롤링 실패:", url, e)
            continue

        existing_font = session.exec(
            select(Font).where(Font.source_url == font_data["source_url"])
        ).first()

        if existing_font:
            print("이미 저장됨:", font_data["name"])
            continue

        font = Font(**font_data)
        session.add(font)

    session.commit()