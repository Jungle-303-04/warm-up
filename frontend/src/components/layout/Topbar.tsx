import { ChevronDown, LogOut, Plus } from "lucide-react";
import { useState } from "react";

import type { UserResponse } from "../../api/auth";

type TopbarProps = {
  currentMonthLabel: string;
  onCreateMeeting: () => void;
  onCreateRetrospective: () => void;
  onLogout: () => void;
  currentUser: UserResponse | null;
  canCreatePage: boolean;
  createDisabledMessage?: string;
};

export function Topbar({
  currentMonthLabel,
  onCreateMeeting,
  onCreateRetrospective,
  onLogout,
  currentUser,
  canCreatePage,
  createDisabledMessage = "오늘 날짜에만 작성할 수 있습니다.",
}: TopbarProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const nickname = currentUser?.nickname ?? "사용자";
  const initial = nickname.trim().charAt(0).toUpperCase() || "U";

  const handleCreateButtonClick = () => {
    if (!canCreatePage) {
      setIsDropdownOpen(false);
      alert(createDisabledMessage);
      return;
    }

    setIsDropdownOpen((prev) => !prev);
  };

  const handleCreateMeeting = () => {
    if (!canCreatePage) {
      alert(createDisabledMessage);
      return;
    }

    setIsDropdownOpen(false);
    onCreateMeeting();
  };

  const handleCreateRetrospective = () => {
    if (!canCreatePage) {
      alert(createDisabledMessage);
      return;
    }

    setIsDropdownOpen(false);
    onCreateRetrospective();
  };

  return (
    <header className="topbar">
      <div>
        <h1 className="topbar-title">캘린더</h1>
        <p className="topbar-subtitle">{currentMonthLabel}</p>
      </div>

      <div className="topbar-actions">
        <div className="user-chip" title={currentUser?.email}>
          <span className="user-chip-avatar">{initial}</span>
          <strong className="user-chip-name">{nickname}</strong>
        </div>

        <button className="logout-button" type="button" onClick={onLogout}>
          <LogOut size={16} />
          <span>로그아웃</span>
        </button>

        <div className="create-menu">
          <button
            className="create-button"
            type="button"
            onClick={handleCreateButtonClick}
            aria-expanded={isDropdownOpen}
            aria-disabled={!canCreatePage}
            title={canCreatePage ? undefined : createDisabledMessage}
          >
            <Plus size={18} />
            <span>새로 만들기</span>
            <ChevronDown size={16} />
          </button>

          {isDropdownOpen && (
            <div className="create-dropdown">
              <button type="button" onClick={handleCreateMeeting}>
                <span className="dropdown-badge meeting">회의</span>
                <div>
                  <div className="dropdown-title">회의 만들기</div>
                  <div className="dropdown-description">
                    오늘 회의록을 작성합니다.
                  </div>
                </div>
              </button>

              <button type="button" onClick={handleCreateRetrospective}>
                <span className="dropdown-badge retrospective">회고</span>
                <div>
                  <div className="dropdown-title">회고 만들기</div>
                  <div className="dropdown-description">
                    오늘 회고를 작성합니다.
                  </div>
                </div>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
