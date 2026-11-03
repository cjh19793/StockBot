// 차트 공통 표시 상수 (폰트/축 색). 데이터와 무관한 스타일 전용.
export const CHART_FONT = "'Pretendard Variable', Pretendard, -apple-system, 'Apple SD Gothic Neo', 'Malgun Gothic', system-ui, sans-serif";

export function axisTick(size = 12) {
  return { fill: "#AAB3C5", fontSize: size, fontFamily: CHART_FONT };
}

export const GRID = "#2A3142";
export const COLORS = {
  price: "#FFB454",
  ma5: "#A78BFA",
  ma20: "#58A6FF",
  band: "#8C97AB",
  up: "#3DDC84",
  down: "#FF6B6B",
};
