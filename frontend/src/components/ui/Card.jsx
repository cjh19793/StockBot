export default function Card({ className = "", children, ...props }) {
  return (
    <div className={`rounded-lg border border-border bg-bg-card p-5 ${className}`} {...props}>
      {children}
    </div>
  );
}
