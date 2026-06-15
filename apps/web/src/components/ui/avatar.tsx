import type { Member } from "../../lib/types";

// 멤버 아바타: avatar_url 있으면 이미지, 없으면 이니셜+색 폴백. member 없으면 "?"(미지정).
export function Avatar({ member, size = 16 }: { member?: Member; size?: number }) {
  const px = `${size}px`;
  if (member?.avatar_url) {
    return (
      <img
        src={member.avatar_url}
        alt={`${member.name} (@${member.login})`}
        title={`${member.name} (@${member.login})`}
        className="shrink-0 rounded-full object-cover"
        style={{ width: px, height: px }}
      />
    );
  }
  return (
    <span
      title={member ? `${member.name} (@${member.login})` : "담당자 미지정"}
      className="grid shrink-0 place-items-center rounded-full font-semibold text-white"
      style={{ width: px, height: px, fontSize: size * 0.56, background: member?.color ?? "#9aa1ab" }}
    >
      {member ? member.name.charAt(0) : "?"}
    </span>
  );
}
