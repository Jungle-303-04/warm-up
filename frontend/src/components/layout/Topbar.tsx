//상단 영역을 담당한다

// 상단 바
// ├─ 현재 페이지 제목
// ├─ 현재 월 표시
// └─ 새로 만들기 버튼
//    ├─ 회의 만들기
//    └─ 회고 만들기


import {ChevronDown, Plus} from "lucide-react";
import {useState} from "react";

type TopbarProps = {
    currentMonthLabel : string;
    onCreateMeeting: () => void;
    onCreateRetrospective: () => void;
};

export function Topbar({
    currentMonthLabel,
    onCreateMeeting,
    onCreateRetrospective,
}: TopbarProps) {
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

    const handleCreateMeeting = () => {
        setIsDropdownOpen(false);
        onCreateMeeting();
    };

    const handleCreateRetrospective = () => {
        setIsDropdownOpen(false);
        onCreateRetrospective();
    };

    return (
        <header className = "topbar">
            <div>
                <h1 className="topbar-title">캘린더</h1>
                <p className = "topbar-subtitle">{currentMonthLabel}</p>
            </div>

            <div className="create-menu">
                <button
                    className = "create-button"
                    type="button"
                    onClick={() => setIsDropdownOpen((prev) => !prev)}
                    aria-expanded={isDropdownOpen}
                >
                    <Plus size={18}/>
                    <span>새로 만들기</span>
                    <ChevronDown size = {16} />
                </button>

                {isDropdownOpen && (
                    <div className = "create-dropdown">
                        <button type="button" onClick = {handleCreateMeeting}>
                            <span className="dropdown-badge meeting">회의</span>
                            <div>
                                <div className="dropdown-title">회의 만들기</div>
                                <div className="dropdown-description">
                                    회의록을 작성합니다.
                                </div>
                            </div>
                        </button>

                        <button type="button" onClick = {handleCreateRetrospective}>
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
            </header>
        );
    }
