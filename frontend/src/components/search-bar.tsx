export function SearchBar({ initialQuery }: Readonly<{ initialQuery: string }>) {
  return (
    <form className="search-bar">
      <input
        type="text"
        name="q"
        defaultValue={initialQuery}
        placeholder="회사명, 업종, 주요 제품으로 검색"
        aria-label="회사 검색"
      />
      <button type="submit">탐색하기</button>
    </form>
  );
}
