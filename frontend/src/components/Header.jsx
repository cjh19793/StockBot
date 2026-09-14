const TABS = [
  { key: "single", label: "단일 분석" },
  { key: "compare", label: "종목 비교" },
  { key: "montecarlo", label: "몬테카를로" },
];

export default function Header({ tab, onTabChange }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-dot" />
        StockBot
      </div>
      <nav className="tabs tabs-desktop">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`tab ${tab === t.key ? "active" : ""}`}
            onClick={() => onTabChange(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <p className="disclaimer-top">모든 결과는 참고용이며 투자 권유가 아닙니다</p>
    </header>
  );
}

export { TABS };
