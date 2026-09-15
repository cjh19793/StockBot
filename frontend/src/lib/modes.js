// /api/modes 조회 실패 시 쓰는 폴백 목록. 백엔드 config.py 의 MODE_CONFIG/MC_CONFIG 미러.
export const FALLBACK_ANALYSIS_MODES = [
  { name: "기본", label: "Daily (Basic)" },
  { name: "단타", label: "5min (Scalping)" },
  { name: "스윙", label: "1hour (Swing)" },
];

export const FALLBACK_MC_MODES = [
  { name: "기본", label: "Basic (7/30/90 days)" },
  { name: "단타", label: "Scalping (1/3/7 days)" },
  { name: "스윙", label: "Swing (7/14/30 days)" },
  { name: "장기", label: "Long-term (90/180/365 days)" },
];
