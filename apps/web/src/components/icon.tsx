import {
  AlignLeft,
  ArrowLeft,
  ArrowUp,
  ArrowUpRight,
  Bell,
  Boxes,
  Calendar,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ChevronsUpDown,
  CircleUserRound,
  Database,
  File,
  FileText,
  FileType,
  Folder,
  FolderGit2,
  Lightbulb,
  Link2,
  ListChecks,
  Loader2,
  LogIn,
  type LucideIcon,
  MessageSquare,
  Monitor,
  Moon,
  MoreVertical,
  Network,
  NotebookText,
  NotebookPen,
  Pencil,
  Plus,
  Search,
  Share2,
  Sparkles,
  StickyNote,
  Sun,
  Trash2,
  Workflow,
  X,
} from "lucide-react";

// board-simple과 동일한 lucide 라인 아이콘. 의미 기반 name → 컴포넌트 매핑.
const ICONS: Record<string, LucideIcon> = {
  hub: Boxes,
  add: Plus,
  add_circle: Plus,
  travel_explore: Search,
  check: Check,
  chat_bubble_outline: MessageSquare,
  auto_awesome: Sparkles,
  arrow_upward: ArrowUp,
  chevron_right: ChevronRight,
  unfold_more: ChevronsUpDown,
  share: Share2,
  notifications: Bell,
  account_circle: CircleUserRound,
  login: LogIn,
  progress_activity: Loader2,
  theme_system: Monitor,
  light_mode: Sun,
  dark_mode: Moon,
  north_east: ArrowUpRight,
  check_circle: CheckCircle2,
  account_tree: Workflow,
  schema: Database,
  checklist: ListChecks,
  calendar_month: Calendar,
  report: NotebookText, // 보고서 (스튜디오)
  mindmap: Network, // 마인드맵 (스튜디오)
  article: StickyNote,
  lightbulb: Lightbulb, // 추천 질문 칩
  note_add: NotebookPen, // 메모 추가
  notebook: NotebookText, // 노트북 대표 아이콘(대시보드/탑바)
  // 소스 타입 아이콘
  folder_code: FolderGit2, // GitHub 저장소
  description: FileText, // Markdown
  text_snippet: AlignLeft, // 텍스트
  picture_as_pdf: FileType, // PDF
  link: Link2,
  close: X, // 모달/다이얼로그 닫기
  more_vert: MoreVertical, // 카드 메뉴
  edit: Pencil, // 이름 변경
  delete: Trash2, // 삭제
  folder: Folder, // 트리 디렉터리
  file: File, // 트리 파일
  chevron_down: ChevronDown, // 트리 펼침
  arrow_back: ArrowLeft, // 대시보드로
};

export function Icon({
  name,
  size = 18,
  strokeWidth = 2,
  className = "",
}: {
  name: string;
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  if (name === "github") {
    // lucide가 brand 아이콘을 제거해 GitHub 마크는 인라인 SVG로 제공한다.
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="currentColor"
        className={className}
        aria-hidden
      >
        <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
      </svg>
    );
  }
  const Glyph = ICONS[name] ?? Boxes;
  return <Glyph size={size} strokeWidth={strokeWidth} className={className} aria-hidden />;
}
