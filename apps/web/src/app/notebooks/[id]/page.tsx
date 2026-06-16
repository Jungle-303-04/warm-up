import { Workspace } from "../../../components/workspace";

// 노트북 화면: 3패널 워크스페이스. Next 15에서 params는 Promise.
export default async function NotebookPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <Workspace notebookId={id} />;
}
