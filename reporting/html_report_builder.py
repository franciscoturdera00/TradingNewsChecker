from html import escape
from typing import Dict, List, Any

def _sentiment_badge(sentiment: str) -> str:
    s = (sentiment or "").lower()
    color = {"positive": "#16a34a", "neutral": "#6b7280", "negative": "#dc2626"}.get(s, "#6b7280")
    bg    = {"positive": "#e9fbe9", "neutral": "#f3f4f6", "negative": "#fdecec"}.get(s, "#f3f4f6")
    label = s.capitalize() if s else "N/A"
    return (
        f'<span style="display:inline-block;padding:4px 10px;border-radius:999px;'
        f'background:{bg};color:{color};font-weight:600;font-size:12px;line-height:1;">{escape(label)}</span>'
    )

def _card_for_position(pos: Dict[str, Any], analysis: Dict[str, Any] | None) -> str:
    t = pos["ticker"]
    qty = f"{pos['qty']:.6f}"
    last_price = pos.get("last_price")
    avg_cost   = pos.get("avg_cost")
    result     = analysis if isinstance(analysis, dict) else None

    bullets   = (result or {}).get("summary_bullets") or []
    sentiment = (result or {}).get("sentiment") or ""
    reasons   = (result or {}).get("reasons") or []
    because   = f" (because: {', '.join(reasons)})" if reasons else ""

    metrics_rows = [
        f"<tr><td style='color:#6b7280;'>Quantity</td><td style='text-align:right;font-weight:600;color:#111827;'>{escape(qty)}</td></tr>",
    ]
    if last_price is not None:
        metrics_rows.append(
            f"<tr><td style='color:#6b7280;'>Last Price</td>"
            f"<td style='text-align:right;font-weight:600;color:#111827;'>{escape(str(last_price))}</td></tr>"
        )
    if avg_cost is not None:
        metrics_rows.append(
            f"<tr><td style='color:#6b7280;'>Avg Cost</td>"
            f"<td style='text-align:right;font-weight:600;color:#111827;'>{escape(str(avg_cost))}</td></tr>"
        )

    bullets_html = "".join(f"<li style='margin:0 0 6px 0;'>{escape(str(b))}</li>" for b in bullets)

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:separate;background:#ffffff;border:1px solid #e5e7eb;
                  border-radius:12px;padding:16px;margin:0 0 16px 0;">
      <tr>
        <td>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <h2 style="margin:0 0 4px 0;font-size:20px;line-height:1.2;color:#111827;">{escape(t)}</h2>
            {_sentiment_badge(sentiment)}
          </div>
          <div style="font-size:12px;color:#6b7280;margin:0 0 12px 0;">News summary & sentiment</div>

          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;margin:0 0 12px 0;">
            <tbody>
              {''.join(metrics_rows)}
            </tbody>
          </table>

          <div style="font-weight:600;color:#111827;margin:8px 0 6px 0;">News Analysis</div>
          {"<ul style='padding-left:20px;margin:0 0 8px 0;'>" + bullets_html + "</ul>" if bullets else "<div style='color:#6b7280;'>No analysis</div>"}
          {f"<div style='color:#374151;font-size:14px;margin-top:6px;'><strong>Overall sentiment:</strong> {escape(sentiment.capitalize() if sentiment else 'N/A')}{escape(because)}</div>" if result else ""}
        </td>
      </tr>
    </table>
    """

def build_portfolio_html_report(
    positions: List[Dict[str, Any]],
    analysis_by_ticker: Dict[str, Dict[str, Any]] | None,
    *,
    title: str = "Daily Portfolio Update",
    subtitle: str = "Top holdings, headlines, and sentiment",
) -> str:
    cards = []
    analysis_by_ticker = analysis_by_ticker or {}
    for pos in positions:
        t = pos["ticker"]
        cards.append(_card_for_position(pos, analysis_by_ticker.get(t)))

    body = "".join(cards) if cards else "<div style='color:#6b7280;'>No positions found.</div>"

    return f"""\
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{escape(title)}</title>
  </head>
  <body style="margin:0;padding:0;background:#f9fafb;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f9fafb;padding:24px 0;">
      <tr>
        <td>
          <table role="presentation" align="center" width="640" cellpadding="0" cellspacing="0" style="margin:0 auto;background:#f9fafb;">
            <tr>
              <td style="padding:0 16px 16px;">
                <h1 style="font-size:24px;line-height:1.25;margin:0 0 12px 0;color:#111827;">{escape(title)}</h1>
                <div style="color:#6b7280;margin:0 0 16px 0;font-size:14px;">{escape(subtitle)}</div>
                {body}
                <div style="color:#9ca3af;font-size:12px;margin-top:16px;">Automated report</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

def build_plaintext_fallback(positions: List[Dict[str, Any]], analysis_by_ticker: Dict[str, Dict[str, Any]] | None) -> str:
    lines = ["Daily Portfolio Update", ""]
    analysis_by_ticker = analysis_by_ticker or {}
    for pos in positions:
        t = pos["ticker"]
        lines.append(f"--- {t} ---")
        lines.append(f"Quantity: {pos['qty']:.6f}")
        if pos.get("last_price") is not None:
            lines.append(f"Last Price: {pos['last_price']}")
        if pos.get("avg_cost") is not None:
            lines.append(f"Avg Cost: {pos['avg_cost']}")
        res = analysis_by_ticker.get(t) or {}
        bullets = res.get("summary_bullets") or []
        sentiment = res.get("sentiment")
        reasons = res.get("reasons") or []
        lines.append("News Analysis:")
        lines.extend(f"- {b}" for b in bullets)
        if sentiment:
            because = f" (because: {', '.join(reasons)})" if reasons else ""
            lines.append(f"Overall sentiment: {sentiment}{because}")
        lines.append("")
    return "\n".join(lines) or "No positions found."
