import {
  AlignLeft,
  ArrowUp,
  ArrowUpRight,
  Bell,
  Boxes,
  Calendar,
  Check,
  CheckCircle2,
  ChevronRight,
  ChevronsUpDown,
  CircleUserRound,
  Database,
  FileText,
  FileType,
  FolderGit2,
  Link2,
  ListChecks,
  Loader2,
  LogIn,
  type LucideIcon,
  MessageSquare,
  Plus,
  Search,
  Share2,
  Sparkles,
  StickyNote,
  Workflow,
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
  north_east: ArrowUpRight,
  check_circle: CheckCircle2,
  account_tree: Workflow,
  schema: Database,
  checklist: ListChecks,
  calendar_month: Calendar,
  article: StickyNote,
  // 소스 타입 아이콘
  folder_code: FolderGit2, // GitHub 저장소
  description: FileText, // Markdown
  text_snippet: AlignLeft, // 텍스트
  picture_as_pdf: FileType, // PDF
  link: Link2,
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
  const Glyph = ICONS[name] ?? Boxes;
  return <Glyph size={size} strokeWidth={strokeWidth} className={className} aria-hidden />;
}
