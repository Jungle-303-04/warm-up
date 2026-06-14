# %%
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import OpenAIEmbeddings

# RAG의 흐름을 조립하는 곳.
"""
1. board 데이터를 가져온다
2. board + detail + task를 하나의 임베딩용 텍스트로 만든다

2. github.service에서 받은 텍스트를 chunk
3. 텍스트가 길면 chunk로 나눈다
4. repository에 저장하라고 넘긴다
5. 검색 요청이 오면 repository에서 관련 chunk를 검색한다
"""


# %%
text = """ 별헤는 밤
계절이 지나가는 하늘에는
가을로 가득 차 있습니다.
나는 아무 걱정도 없이
가을 속의 별들을 다 헤일 듯합니다.
가슴 속에 하나 둘 새겨지는 별을
이제 다 못 헤는 것은
쉬이 아침이 오는 까닭이요,
내일 밤이 남은 까닭이요,
아직 나의 청춘이 다하지 않은 까닭입니다.
별 하나에 추억과
별 하나에 사랑과
별 하나에 쓸쓸함과
별 하나에 동경과
별 하나에 시와
별 하나에 어머니, 어머니,
어머님, 나는 별 하나에 아름다운 말 한마디씩 불
러봅니다. 소학교때 책상을 같이 했던 아이들의
이름과, 패, 경, 옥 이런 이국소녀들의 이름과 벌
써 애기 어머니 된 계집애들의 이름과, 가난한 이
웃사람들의 이름과, 비둘기, 강아지, 토끼, 노새,
노루, 「프란시스·쟘 」 「라이너·마리아·릴
케」 이런 시인의 이름을 불러봅니다.

이네들은 너무나 멀리 있습니다.
별이 아슬히 멀 듯이,
어머님,
그리고 당신은 멀리 북간도에 계십니다.
나는 무엇인지 그리워
이 많은 별빛이 나린 언덕 위에
내 이름자를 써보고,
흙으로 덮어 버리었습니다.
딴은 밤을 새워 우는 벌레는
부끄러운 이름을 슬퍼하는 까닭입니다.
그러나 겨울이 지나고 나의 별에도 봄이 오면
무덤 위에 파란 잔디가 피어나듯이
내 이름자 묻힌 언덕 위에도
자랑처럼 풀이 무성할 게외다.

1941.11.5

진짜 바뀌는게 맞음??!!!
"""


# %%
# TODO: board + detail + task를 하나의 임베딩용 텍스트로
def embedding_from_db():
    return "A"




# %%
# chunk text
def text_splitter(merged_text):

    split_texts = RecursiveCharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=20,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    text_list = split_texts.split_text(merged_text)
    return text_list

print(len(text_splitter(text)))
print([len(chunk) for chunk in text_splitter(text)])

# %%



# %%
# create
# TODO: repository에 저장하라고 넘김 == 벡터DB



# %%
# get
# TODO: 검색 요청이 오면 repository==vector db에서 관련 chunk를 검색




# %%
## embedding the chunked text

def create_embedding_model():
    return OpenAIEmbeddings(model='text-embedding-3-large')