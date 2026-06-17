import { useEffect, useState } from "react";

function TypingWaitingMessage({ lines }) {
  const fixedLines = lines.slice(0, -1);
  const typingLine = lines.at(-1) ?? "";
  const [typedLine, setTypedLine] = useState("");

  useEffect(() => {
    let currentIndex = 0;
    const typingTimer = setInterval(() => {
      currentIndex += 1;
      setTypedLine(typingLine.slice(0, currentIndex));

      if (currentIndex >= typingLine.length) {
        clearInterval(typingTimer);
      }
    }, 70);

    return () => {
      clearInterval(typingTimer);
    };
  }, [typingLine]);

  return (
    <div className="space-y-1">
      {fixedLines.map((line) => (
        <p className="text-base font-semibold text-black" key={line}>
          {line}
        </p>
      ))}
      <p className="text-base font-semibold text-black">
        {typedLine}
        <span className="ml-0.5 inline-block h-4 w-px translate-y-0.5 animate-pulse bg-black" />
      </p>
    </div>
  );
}

export default TypingWaitingMessage;
