import { ChevronDown, LogOut, Plus } from "lucide-react";
import { useState } from "react";


// CalendarPgae가 필요한 값을 준다
type TopbarProps = {
  currentMonthLabel: string; // 몇년 몇월인지
  onCreateMeeting: () => void; // 회의 만들기 눌렀을 떄 할 일
  onCreateRetrospective: () => void; // 회고 만들기 눌렀을 떄 할일
  onLogout: () => void; // 로그아웃 눌렀을 때 할 일
};

export function Topbar({
  currentMonthLabel,
  onCreateMeeting,
  onCreateRetrospective,
  onLogout,
}: TopbarProps) {
  // 새로 만들기 버튼을 누르면 회의/회고 선택 드롭다운을 열고 닫습니다.
  const [isDropdownOpen, setIsDropdownOpen] = useState(false); // 처음엔 새로 만들기 메뉴 닫혀 있음 (false)

 //회의 만들기 누르면 드롭다운 닫기, 회의 작성 모달 열기 두 개

  const handleCreateMeeting = () => {
    // 드롭다운을 닫고 부모(CalendarPage)에게 회의 모달을 열라고 알립니다.
    setIsDropdownOpen(false);
    onCreateMeeting(); // 부모에게 회의 모달 열라고 알림
  };

  const handleCreateRetrospective = () => {
    // 드롭다운을 닫고 부모(CalendarPage)에게 회고 모달을 열라고 알립니다.
    setIsDropdownOpen(false);
    onCreateRetrospective(); // 부모에게 회고 모달 열라고 알림
  };

  return (
    <header className="topbar">
      <div>
        <h1 className="topbar-title">캘린더</h1>
        <p className="topbar-subtitle">{currentMonthLabel}</p>
      </div>

      <div className="topbar-actions">
        <button className="logout-button" type="button" onClick={onLogout}>
          <LogOut size={16} />
          <span>로그아웃</span>
        </button>

        <div className="create-menu">
          <button
            className="create-button"
            type="button"
            onClick={() => setIsDropdownOpen((prev) => !prev)}
            aria-expanded={isDropdownOpen}
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
                    회의록을 작성합니다.
                  </div>
                </div>
              </button>

              <button type="button" onClick={handleCreateRetrospective}>
                <span className="dropdown-badge retrospective">회고</span>
                <div>
                  <div className="dropdown-title">회고 만들기</div>
                  <div className="dropdown-description">
                    하루 회고를 작성합니다.
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
