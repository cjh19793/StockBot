const ITEMS = [
  {
    key: "single",
    label: "분석",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 3v18h18" />
        <path d="M7 14l3-3 3 3 5-6" />
      </svg>
    ),
  },
  {
    key: "compare",
    label: "비교",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="7" height="18" />
        <rect x="14" y="8" width="7" height="13" />
      </svg>
    ),
  },
  {
    key: "montecarlo",
    label: "몬테카를로",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 3" />
      </svg>
    ),
  },
];

export default function BottomNav({ tab, onTabChange }) {
  return (
    <nav className="bottom-nav">
      {ITEMS.map((item) => (
        <button
          key={item.key}
          type="button"
          className={`nav-item ${tab === item.key ? "active" : ""}`}
          onClick={() => onTabChange(item.key)}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
