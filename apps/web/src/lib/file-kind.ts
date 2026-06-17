// 파일 경로/확장자 판별의 단일 출처.

const EXT_ICON_MAP: Record<string, string> = {
  md: "description",
  markdown: "description",
  mdx: "description",
  txt: "text_snippet",
  rst: "text_snippet",
  pdf: "picture_as_pdf",
  json: "file_json",
  jsonc: "file_json",
  yml: "file_json",
  yaml: "file_json",
  toml: "file_json",
  ini: "file_json",
  cfg: "file_json",
  env: "file_json",
  csv: "file_spreadsheet",
  tsv: "file_spreadsheet",
  sh: "file_terminal",
  bash: "file_terminal",
  zsh: "file_terminal",
  svg: "file_image",
  png: "file_image",
  jpg: "file_image",
  jpeg: "file_image",
  gif: "file_image",
  webp: "file_image",
};

const EXT_TO_LANG: Record<string, string> = {
  py: "python",
  pyi: "python",
  js: "javascript",
  jsx: "javascript",
  mjs: "javascript",
  cjs: "javascript",
  ts: "typescript",
  tsx: "typescript",
  json: "json",
  jsonc: "json",
  html: "xml",
  htm: "xml",
  xml: "xml",
  svg: "xml",
  css: "css",
  scss: "scss",
  less: "less",
  sh: "bash",
  bash: "bash",
  zsh: "bash",
  yml: "yaml",
  yaml: "yaml",
  toml: "ini",
  ini: "ini",
  cfg: "ini",
  sql: "sql",
  go: "go",
  rs: "rust",
  java: "java",
  kt: "kotlin",
  c: "c",
  h: "c",
  cpp: "cpp",
  cc: "cpp",
  hpp: "cpp",
  cs: "csharp",
  rb: "ruby",
  php: "php",
  swift: "swift",
  dockerfile: "dockerfile",
};

const CODE_EXTS = new Set([
  "py",
  "pyi",
  "ipynb",
  "js",
  "jsx",
  "mjs",
  "cjs",
  "ts",
  "tsx",
  "go",
  "rs",
  "java",
  "kt",
  "kts",
  "c",
  "h",
  "cpp",
  "cc",
  "hpp",
  "cs",
  "rb",
  "php",
  "swift",
  "scala",
  "dart",
  "lua",
  "r",
  "sql",
  "html",
  "htm",
  "xml",
  "css",
  "scss",
  "less",
  "vue",
  "svelte",
]);

const SPECIAL_CODE_FILES = new Set(["dockerfile", "makefile"]);

export function fileNameOf(path?: string | null): string {
  if (!path) return "";
  return path.toLowerCase().split("/").pop() ?? "";
}

export function fileExtensionOf(path?: string | null): string {
  const name = fileNameOf(path);
  return name.includes(".") ? name.split(".").pop()! : "";
}

export function isCodePath(path?: string | null): boolean {
  const name = fileNameOf(path);
  if (!name) return false;
  return SPECIAL_CODE_FILES.has(name) || name.endsWith(".dockerfile") || CODE_EXTS.has(fileExtensionOf(name));
}

export function languageOfPath(path?: string | null): string | undefined {
  const name = fileNameOf(path);
  if (!name) return undefined;
  if (SPECIAL_CODE_FILES.has(name)) return EXT_TO_LANG[name];
  return EXT_TO_LANG[fileExtensionOf(name)];
}

export function fileIconForPath(path?: string | null): string {
  const name = fileNameOf(path);
  if (!name) return "file";
  const ext = fileExtensionOf(name);
  if (ext in EXT_ICON_MAP) return EXT_ICON_MAP[ext];
  if (isCodePath(name)) return "file_code";
  return "file";
}
