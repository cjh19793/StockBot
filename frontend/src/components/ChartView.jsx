import { useState } from "react";

export default function ChartView({ src, alt }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  return (
    <div className="chart-view">
      {!loaded && (
        <div className="chart-placeholder">
          {failed ? (
            <span className="t1" style={{ color: "var(--negative)" }}>차트를 불러오지 못했습니다</span>
          ) : (
            <>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M3 3v18h18" />
                <path d="M7 14l3-3 3 3 5-6" />
              </svg>
              <span className="t1">차트 불러오는 중...</span>
            </>
          )}
        </div>
      )}
      <img
        key={src}
        src={src}
        alt={alt}
        style={{ display: loaded ? "block" : "none" }}
        onLoad={() => { setLoaded(true); setFailed(false); }}
        onError={() => { setLoaded(false); setFailed(true); }}
      />
    </div>
  );
}
