export function Hint({ children }) {
  return <p className="text-[13px] text-ink-faint">{children}</p>;
}

export function ErrorMessage({ children }) {
  return (
    <p className="rounded-md border border-down/30 bg-down/10 px-4 py-3 text-[13px] text-down">
      {children}
    </p>
  );
}
