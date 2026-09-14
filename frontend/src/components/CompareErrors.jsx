export default function CompareErrors({ errors }) {
  if (errors.length === 0) return null;

  return (
    <div className="error-banner">
      <h3>분석 실패한 종목 ({errors.length}개)</h3>
      <ul>
        {errors.map((e) => (
          <li key={e.ticker}>
            <strong>{e.ticker}</strong> — {e.error}
          </li>
        ))}
      </ul>
    </div>
  );
}
