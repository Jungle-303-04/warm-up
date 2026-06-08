import { useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");

  const handleClick = async () => {
    const res = await fetch("http://localhost:8000/health");
    const data = await res.json();

    setMessage(data.status);
  };

  return (
    <>
      <h1>AI Font Recommendation</h1>

      <input placeholder="브랜드 설명 입력" />
      <button onClick={handleClick}>추천받기</button>

      <div>
        추천 결과 영역
        <p>{message}</p>
      </div>
    </>
  );
}

export default App;
