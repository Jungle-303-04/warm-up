"use client";

import { extractPdfText } from "./pdf";
import type { SourceCreate } from "./types";

// 드롭/선택된 File 하나를 SourceCreate 바디로 변환함
// - .pdf → pdfjs 로 텍스트 추출(kind:"pdf")
// - .md/.markdown → file.text()(kind:"md")
// - 그 외 텍스트(.txt 포함) → file.text()(kind:"text")
export async function fileToSourceCreate(file: File): Promise<SourceCreate> {
  const name = file.name;
  const lower = name.toLowerCase();
  const isPdf = lower.endsWith(".pdf") || file.type === "application/pdf";
  const isMd = lower.endsWith(".md") || lower.endsWith(".markdown");

  if (isPdf) {
    const content = await extractPdfText(file);
    return { kind: "pdf", title: name, content };
  }
  if (isMd) {
    const content = await file.text();
    return { kind: "md", title: name, content };
  }
  // .txt 및 기타 텍스트 파일.
  const content = await file.text();
  return { kind: "text", title: name, content };
}
