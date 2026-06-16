import { AuthGate } from "../../../components/auth-gate";
import { Workspace } from "../../../components/workspace";

// 노트북 화면: 3패널 워크스페이스. Next 15에서 params는 Promise.
// 미로그인 시 로그인 화면으로 게이트.
export default async function NotebookPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <AuthGate>
      <Workspace notebookId={id} />
    </AuthGate>
  );
}
