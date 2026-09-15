export default function TickerInput({ id, value, onChange, placeholder = "예: AAPL", ...props }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-border bg-bg-raised px-3 py-2.5 focus-within:border-amber-dim">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="shrink-0 text-ink-faint">
        <circle cx="11" cy="11" r="7" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <input
        id={id}
        type="text"
        inputMode="text"
        autoCapitalize="characters"
        autoComplete="off"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-transparent font-mono text-sm text-ink placeholder:text-ink-faint focus:outline-none"
        {...props}
      />
    </div>
  );
}
