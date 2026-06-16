"use client";

// 클라이언트에서 PDF를 텍스트로 추출한다. pdfjs-dist 동적 import + CDN 워커.
// 추출 실패 시 throw 하므로 호출부에서 사용자에게 에러를 표시한다.
export async function extractPdfText(file: File): Promise<string> {
  const pdfjs = await import("pdfjs-dist");
  // 번들러 워커 설정 대신 버전 일치 CDN 워커를 사용(요구사항).
  pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`;

  const buffer = await file.arrayBuffer();
  const doc = await pdfjs.getDocument({ data: buffer }).promise;

  const pages: string[] = [];
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i);
    const content = await page.getTextContent();
    const text = content.items
      .map((item) => ("str" in item ? item.str : ""))
      .join(" ");
    pages.push(text);
  }
  await doc.destroy();

  const result = pages.join("\n\n").trim();
  if (!result) throw new Error("PDF에서 텍스트를 추출하지 못했습니다 (이미지 PDF일 수 있음)");
  return result;
}
