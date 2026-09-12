"""분석 리포트 + 차트 생성 — 텔레그램 래퍼.

계산: engine.run_analysis / 리포트 포맷: report_format.format_analysis_report
차트: charts.build_chart. 기존 analyze() 시그니처와 동작(오류 시 (None, None))은 유지.
"""
import logging

from charts import build_chart
from engine import run_analysis
from errors import AnalysisError
from report_format import format_analysis_report

log = logging.getLogger(__name__)


def analyze(ticker: str, mode: str = "기본"):
    """(리포트 문자열, PNG BytesIO). 데이터 없거나 오류 시 (None, None)."""
    try:
        result = run_analysis(ticker, mode)
        report = format_analysis_report(result)
        chart_buf = build_chart(
            result.df,
            ticker=result.ticker,
            label=result.label,
            now_str=result.now_str,
            market=result.market,
            chart_title=result.chart_title,
            target_price=result.target_price,
            stop_loss=result.stop_loss,
            buy_score=result.buy_score,
            sell_score=result.sell_score,
            bar_width=result.bar_width,
        )
        return report, chart_buf
    except AnalysisError:
        return None, None
    except Exception:
        log.exception("분석 실패: %s (%s)", ticker, mode)
        return None, None
