import { useEffect, useState } from "react";
import { api } from "./api/client";

function App() {
  // FastAPI 서버 상태를 저장하는 state
  // 처음에는 아직 확인 전이므로 "checking..."으로 표시
  const [apiStatus, setApiStatus] = useState("checking...");

  // PostgreSQL DB 연결 상태를 저장하는 state
  const [dbStatus, setDbStatus] = useState("checking...");

  // pgvector 확장 설치/연결 상태를 저장하는 state
  const [pgvectorStatus, setPgvectorStatus] = useState("checking...");

  useEffect(() => {
    // 컴포넌트가 처음 화면에 렌더링될 때 한 번만 실행됨

    // 1. FastAPI 서버가 살아있는지 확인
    api
      .get("/health")
      .then((res) => setApiStatus(res.data.status))
      .catch(() => setApiStatus("error"));

    // 2. PostgreSQL 연결 상태 확인
    api
      .get("/db-health")
      .then((res) => setDbStatus(res.data.status))
      .catch(() => setDbStatus("error"));

    // 3. pgvector 확장 상태 확인
    // res.data.extension 값이 있으면 표시하고,
    // 없으면 "not found"로 표시
    api
      .get("/pgvector-health")
      .then((res) => setPgvectorStatus(res.data.extension ?? "not found"))
      .catch(() => setPgvectorStatus("error"));
  }, []);

  return (
    <main style={{ padding: 40, fontFamily: "sans-serif" }}>
      {/* 서비스 이름 */}
      <h1>TeamLog</h1>

      {/* 서비스 설명 */}
      <p>캘린더 기반 회의/회고 협업툴</p>

      {/* 백엔드/DB/확장 연결 상태 표시 영역 */}
      <h2>연결 상태</h2>
      <ul>
        <li>FastAPI: {apiStatus}</li>
        <li>PostgreSQL: {dbStatus}</li>
        <li>pgvector: {pgvectorStatus}</li>
      </ul>
    </main>
  );
}

export default App;