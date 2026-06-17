const fallbackFontFamily = "\"Pretendard\", sans-serif";

function createWebFontFamilyName(font) {
  const fontId = font?.id ?? "unknown";
  const fontName = font?.name ?? "font";

  return `fboard-${fontId}-${fontName}`.replace(/[^a-zA-Z0-9_-]/g, "-");
}

function getWebFontUrl(font) {
  const webfonts = Array.isArray(font?.webfonts) ? font.webfonts : [];
  const firstWebFont = webfonts.find((webfont) => {
    return typeof webfont.url === "string" && webfont.url.trim() !== "";
  });

  return firstWebFont?.url.trim() ?? null;
}

export function hasWebFontUrl(font) {
  return Boolean(getWebFontUrl(font));
}

function getWebFontWeight(font) {
  const webfonts = Array.isArray(font?.webfonts) ? font.webfonts : [];
  const firstWebFont = webfonts.find((webfont) => {
    return typeof webfont.url === "string" && webfont.url.trim() !== "";
  });

  return firstWebFont?.weight ?? 400;
}

export function registerWebFont(font) {
  const fontUrl = getWebFontUrl(font);

  if (!fontUrl || typeof document === "undefined") {
    return null;
  }

  const fontFamily = createWebFontFamilyName(font);
  const styleId = `webfont-${fontFamily}`;

  if (!document.getElementById(styleId)) {
    const styleElement = document.createElement("style");
    styleElement.id = styleId;
    styleElement.textContent = `
@font-face {
  font-family: "${fontFamily}";
  src: url("${fontUrl}");
  font-weight: ${getWebFontWeight(font)};
  font-style: normal;
  font-display: swap;
}
`;

    document.head.appendChild(styleElement);
  }

  return fontFamily;
}

export function createWebFontStyle(font) {
  const fontFamily = registerWebFont(font);

  if (!fontFamily) {
    return {
      fontFamily: fallbackFontFamily,
    };
  }

  return {
    fontFamily: `"${fontFamily}", "Pretendard", sans-serif`,
  };
}
