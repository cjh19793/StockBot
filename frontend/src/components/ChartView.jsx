import { useState } from "react";

export default function ChartView({ src, alt }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  return (
    <div className="chart-view">
      {!loaded && !failed && <p className="chart-status">차트 불러오는 중...</p>}
      {failed && <p className="chart-status error">차트를 불러오지 못했습니다.</p>}
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
