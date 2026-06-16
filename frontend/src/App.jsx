import { useState } from "react";
import Header from "./components/Header";

function App() {
  const [message, setMessage] = useState("");

  const handleClick = async () => {
    const res = await fetch("http://localhost:8000/health");
    const data = await res.json();

    setMessage(data.status);
  };

  return (
    <div className="min-h-screen w-full max-w-[1024px] rounded-[10px] bg-white">
      <Header />

      <main className="p-6">
        <h1 className="text-2xl font-semibold text-gray-950">
          AI Font Recommendation
        </h1>

        <div className="mt-8 flex gap-3">
          <input
            className="min-h-11 flex-1 rounded-md border border-gray-200 px-4 text-sm outline-none focus:border-gray-400"
            placeholder="브랜드 설명 입력"
          />
          <button
            className="min-h-11 rounded-md bg-gray-950 px-5 text-sm font-medium text-white"
            onClick={handleClick}
          >
            추천받기
          </button>
        </div>

        <div className="mt-8 rounded-md border border-gray-200 p-5 text-sm text-gray-700">
          추천 결과 영역
          <p className="mt-2 text-gray-950">{message}</p>
        </div>
      </main>
    </div>
  );
}

export default App;
