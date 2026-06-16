function Header() {
  return (
    <header className="relative rounded-t-md bg-white px-6 py-5 shadow-[0_4px_4px_-4px_rgba(15,23,42,0.18)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-7">
          <span className="font-['Zodiak'] text-[40pt] font-extrabold italic leading-none text-black">
            f
          </span>
          <span className="text-[30px] font-normal leading-none text-black">
            Board
          </span>
        </div>

        <div className="flex items-center gap-5">
          <button
            className="h-11 rounded-md border border-gray-200 px-8 text-sm font-normal text-black"
            type="button"
          >
            글쓰기
          </button>
          <button className="text-[10px] font-semibold text-black" type="button">
            관리자
          </button>
        </div>
      </div>

      <span className="absolute bottom-0 left-[110px] h-px w-20 bg-gray-500" />
    </header>
  );
}

export default Header;
