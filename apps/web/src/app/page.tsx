import { AuthGate } from "../components/auth-gate";
import { Dashboard } from "../components/dashboard";

// 홈(대시보드): 노트북 카드 그리드. 미로그인 시 로그인 화면으로 게이트.
export default function Home() {
  return (
    <AuthGate>
      <Dashboard />
    </AuthGate>
  );
}
