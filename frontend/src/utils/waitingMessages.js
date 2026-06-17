export const waitingMessages = [
  [
    "고딕체는 명확함을, 손글씨체는 친근함을 전달하는 경우가 많아요.",
    "문장의 분위기를 분석하는 중...",
  ],
  [
    "좋은 폰트는 내용을 꾸미기보다 돋보이게 해요.",
    "어울리는 폰트를 탐색하는 중...",
  ],
  [
    "굵기 하나만 달라도 분위기는 크게 바뀔 수 있어요.",
    "폰트 특징을 분석하는 중...",
  ],
];

export function shuffleWaitingMessages() {
  const shuffledMessages = [...waitingMessages];

  for (let index = shuffledMessages.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    const currentMessage = shuffledMessages[index];

    shuffledMessages[index] = shuffledMessages[randomIndex];
    shuffledMessages[randomIndex] = currentMessage;
  }

  return shuffledMessages;
}
