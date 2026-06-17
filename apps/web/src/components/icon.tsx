// Google Material Symbols는 기본적으로 lowercase 스네이크 케이스 이름을 사용합니다.
// 기존 lucide 매핑용 이름 중 머티리얼 심볼과 호환되지 않는 항목들을 오버라이드합니다.
const SYMBOL_NAME_OVERRIDES: Record<string, string> = {
  hub: "widgets", // Boxes 대신 위젯
  theme_system: "settings_brightness",
  progress_activity: "autorenew", // 로딩 스피너
  refresh: "sync",
  save_note: "note_add",
  folder_code: "folder",
  file_code: "code",
  file_json: "terminal",
  file_terminal: "terminal",
  file_image: "image",
  file_spreadsheet: "table_chart",
  audio_magic_eraser: "cleaning_services",
  cards_star: "style",
  dock_to_left: "left_panel_close",
  dock_left_open: "left_panel_open",
  dock_to_right: "right_panel_close",
  dock_right_open: "right_panel_open",
  audio: "audio_file",
  article: "article",
  keep: "push_pin",
  delete: "delete",
  edit: "edit",
  copy: "content_copy", // Material Symbols에 'copy' 글리프가 없어 글자가 노출되던 문제 수정
};

export function Icon({
  name,
  size = 18,
  strokeWidth = 1.5, // 기본 획 두께를 약간 얇게 조정하여 프리미엄 룩 완성
  className = "",
}: {
  name: string;
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  if (name === "github") {
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

  const symbol = SYMBOL_NAME_OVERRIDES[name] ?? name;

  // strokeWidth 1.5 -> wght 300, 2 -> wght 350, 2.5 -> wght 400
  const wght = strokeWidth <= 1.5 ? 300 : strokeWidth >= 2.5 ? 400 : 350;

  return (
    <span
      className={`material-symbols-outlined select-none inline-flex items-center justify-center ${className}`}
      style={{
        fontSize: `${size}px`,
        width: `${size}px`,
        height: `${size}px`,
        fontVariationSettings: `'FILL' 0, 'wght' ${wght}, 'GRAD' 0, 'opsz' 20`,
      }}
      aria-hidden
    >
      {symbol}
    </span>
  );
}
