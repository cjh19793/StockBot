const FEATURES = [
  {
    tag: "RSI",
    title: "과매수 · 과매도 탐지",
    desc: "14일 기준 RSI로 추세 과열 여부를 판단하고 반전 가능 구간을 짚어냅니다.",
  },
  {
    tag: "MACD",
    title: "추세 전환 포착",
    desc: "골든크로스 · 데드크로스 발생 시점을 감지해 매수/매도 신호에 반영합니다.",
  },
  {
    tag: "MC",
    title: "몬테카를로 시뮬레이션",
    desc: "과거 가격 구간을 부트스트랩 표본추출해 보유기간별 승률과 수익 분포를 계산합니다.",
  },
  {
    tag: "종합",
    title: "종합점수",
    desc: "기술적 분석 · 시장환경 · 리스크 · 펀더멘털을 가중합해 하나의 점수로 정리합니다.",
  },
];

export default function FeatureGrid() {
  return (
    <section id="features" className="border-b border-border py-16 sm:py-20">
      <div className="mb-3.5 font-mono text-[12.5px] text-amber">기능</div>
      <h2 className="max-w-[560px] text-[26px] font-semibold tracking-tight sm:text-[30px]">
        여러 지표를 따로 안 봐도 됩니다
      </h2>
      <p className="mt-4 max-w-[520px] text-[15px] text-ink-dim">
        각 지표를 직접 해석하는 대신, StockBot이 조합해서 하나의 결론으로 정리해 드립니다.
      </p>
      <div className="mt-12 grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div key={f.tag} className="bg-bg-card p-6">
            <div className="mb-3.5 font-mono text-lg text-amber">{f.tag}</div>
            <h3 className="mb-2 text-[15px] font-semibold">{f.title}</h3>
            <p className="text-[13px] leading-relaxed text-ink-dim">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
