function PreservedText({ className = "", lineGapClassName = "mt-0", style, text }) {
  const lines = String(text ?? "").split("\n");

  return (
    <p className={className} style={style}>
      {lines.map((line, index) => {
        const lineKey = `${index}-${line}`;
        const spacingClassName = index === 0 ? "" : lineGapClassName;
        const isEmptyLine = line === "";

        if (isEmptyLine) {
          return (
            <span
              aria-hidden="true"
              className={["block h-[0.45em]", spacingClassName].join(" ")}
              key={lineKey}
            />
          );
        }

        return (
          <span
            className={["block break-words", spacingClassName].join(" ")}
            key={lineKey}
          >
            {line}
          </span>
        );
      })}
    </p>
  );
}

export default PreservedText;
