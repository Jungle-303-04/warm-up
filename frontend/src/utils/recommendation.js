import { createWebFontStyle, hasWebFontUrl } from "./webFont";

export function createRecommendationFromPost(post) {
  const font = post.font ?? {};
  const isPaid = font.is_paid ?? font.isPaid;

  return {
    downloadUrl: font.download_url ?? font.downloadUrl ?? "",
    id: font.id,
    isDefaultFontApplied: !hasWebFontUrl(font),
    isPaid,
    license: font.license ?? "",
    licenseSummary: font.license_summary ?? font.licenseSummary ?? [],
    name: font.name ?? "",
    previewFontStyle: createWebFontStyle(font),
    reason: post.recommend_reason ?? "",
    source: font.source ?? "",
    sourceUrl: font.source_url ?? font.sourceUrl,
    tags: font.tags ?? [],
    usage: font.category ?? "",
    webfonts: font.webfonts ?? [],
  };
}

export function createRecommendationFromResponse(recommendationResponse) {
  const selectedFont = recommendationResponse.font ?? {};
  const selection = recommendationResponse.selection ?? {};
  const isPaid = selectedFont.is_paid ?? selectedFont.isPaid;

  return {
    downloadUrl: selectedFont.download_url ?? "",
    id: selectedFont.id ?? selection.font_id,
    isDefaultFontApplied: !hasWebFontUrl(selectedFont),
    isPaid,
    license: selectedFont.license ?? "",
    licenseSummary: selectedFont.license_summary ?? selectedFont.licenseSummary ?? [],
    name: selectedFont.name ?? "",
    previewFontStyle: createWebFontStyle(selectedFont),
    reason:
      selection.display_reason ??
      selection.reason ??
      selectedFont.description ??
      "",
    source: selectedFont.source ?? "",
    sourceUrl: selectedFont.source_url ?? selectedFont.sourceUrl,
    tags: selectedFont.tags ?? [],
    usage: selectedFont.category ?? "",
    webfonts: selectedFont.webfonts ?? [],
  };
}
