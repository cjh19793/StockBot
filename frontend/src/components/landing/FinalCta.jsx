import Link from "next/link";

export default function FinalCta() {
  return (
    <section className="flex flex-col items-center gap-5 py-16 text-center sm:py-20">
      <h2 className="text-[26px] font-semibold tracking-tight sm:text-[30px]">지금 바로 분석을 시작하세요</h2>
      <p className="max-w-[440px] text-[15px] text-ink-dim">
        티커 하나만 입력하면 지표 계산부터 매수/매도 신호까지 몇 초 안에 확인할 수 있습니다.
      </p>
      <Link href="/analyze" className="rounded-md bg-amber px-7 py-3.5 font-semibold text-[#1A1000] transition-opacity hover:opacity-90">
        웹에서 바로 시작
      </Link>
    </section>
  );
}
