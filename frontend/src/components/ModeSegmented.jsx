export default function ModeSegmented({ modes, value, onChange, ariaLabel }) {
  return (
    <div role="radiogroup" aria-label={ariaLabel} className="flex rounded-md border border-border bg-bg-raised p-1">
      {modes.map((m) => (
        <button
          key={m.name}
          type="button"
          role="radio"
          aria-checked={value === m.name}
          onClick={() => onChange(m.name)}
          className={`rounded px-3 py-1.5 font-mono text-[12.5px] transition-colors ${
            value === m.name ? "bg-amber text-[#1A1000] font-semibold" : "text-ink-dim hover:text-ink"
          }`}
        >
          {m.name}
        </button>
      ))}
    </div>
  );
}
