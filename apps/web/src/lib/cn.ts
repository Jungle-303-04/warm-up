// 조건부 className 결합 헬퍼(falsy 제거). 템플릿 리터럴 분기를 대체함
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
