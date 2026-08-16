"""
Digest API — POST /api/digest
Builds and sends weekly email digest via Resend.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import verify_token

router = APIRouter()


class DigestRequest(BaseModel):
    recipient_email: str
    store_name: str
    total_revenue: float
    revenue_change_pct: float
    total_orders: int
    wellness_score: int
    wellness_interpretation: str
    priority_alerts: list[dict]
    at_risk_customers: int
    top_combo: str
    forecast_next_7d: float
    seo_tip: str
    week_start: str
    week_end: str


@router.post("/digest")
def digest(payload: DigestRequest, token: str = Depends(verify_token)):
    resend_key = os.environ.get("RESEND_API_KEY")
    if not resend_key:
        return {"status": "skipped", "reason": "No RESEND_API_KEY configured"}

    import resend as resend_lib
    resend_lib.api_key = resend_key

    revenue_sign = "+" if payload.revenue_change_pct >= 0 else ""
    alert_count = len(payload.priority_alerts)

    html_content = f"""
    <div style="font-family: Inter, Segoe UI, sans-serif; max-width: 600px; margin: 0 auto; color: #1C1C3B;">
      <div style="background: linear-gradient(160deg, #423A8E, #2D2680); color: white; padding: 32px; border-radius: 16px 16px 0 0;">
        <h1 style="margin: 0; font-size: 24px;"> {payload.store_name} — Weekly Report</h1>
        <p style="margin: 8px 0 0; opacity: 0.7; font-size: 14px;">{payload.week_start} → {payload.week_end}</p>
      </div>
      <div style="background: #F4F6FB; padding: 24px; border-radius: 0 0 16px 16px;">
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #E5E7EB;">
          <div style="font-size: 12px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Revenue This Week</div>
          <div style="font-size: 32px; font-weight: 800; color: #423A8E; margin-top: 4px;">${payload.total_revenue:,.0f}</div>
          <div style="font-size: 14px; color: {'#198754' if payload.revenue_change_pct >= 0 else '#DC3545'}; margin-top: 4px;">
            {revenue_sign}{payload.revenue_change_pct:.1f}% vs last week · {payload.total_orders:,} orders
          </div>
        </div>
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #E5E7EB;">
          <div style="font-size: 12px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Store Wellness</div>
          <div style="font-size: 32px; font-weight: 800; color: {'#198754' if payload.wellness_score >= 70 else ('#FFC107' if payload.wellness_score >= 50 else '#DC3545')}; margin-top: 4px;">{payload.wellness_score}/100</div>
          <div style="font-size: 14px; color: #6B7280; margin-top: 4px;">{payload.wellness_interpretation}</div>
        </div>
    """

    if payload.priority_alerts:
        html_content += f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #E5E7EB; border-left: 4px solid #DC3545;">
          <div style="font-size: 12px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Priority Alerts ({alert_count})</div>
        """
        for alert in payload.priority_alerts[:5]:
            html_content += f"""
          <div style="margin-top: 10px; padding: 10px; background: #FFF1F2; border-radius: 8px;">
            <div style="font-weight: 700; color: #DC3545; font-size: 14px;">{alert.get('Product_Name', alert.get('Product_ID', 'Unknown'))} — {alert.get('Health_Status', 'ALERT')}</div>
            <div style="font-size: 13px; color: #6B7280; margin-top: 2px;">{alert.get('Health_Explanation', 'Needs attention')}</div>
          </div>
            """
        html_content += "</div>"

    html_content += f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #E5E7EB;">
          <div style="font-size: 12px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Insights</div>
          <div style="font-size: 14px; color: #1C1C3B; margin-top: 8px; line-height: 1.6;">
            <strong>Top Combo:</strong> {payload.top_combo}<br>
            <strong>At-Risk Customers:</strong> {payload.at_risk_customers} haven't purchased in 30+ days<br>
            <strong>7-Day Forecast:</strong> ${payload.forecast_next_7d:,.0f}<br>
            <strong>SEO Tip:</strong> {payload.seo_tip}
          </div>
        </div>
        <div style="text-align: center; margin-top: 24px;">
          <a href="https://navigare.vercel.app/dashboard" style="background: #423A8E; color: white; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 14px;">View Full Dashboard</a>
        </div>
        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #6B7280;">
          Sent automatically by Navigare · <a href="https://navigare.vercel.app" style="color: #423A8E;">navigare.vercel.app</a>
        </div>
      </div>
    </div>
    """

    try:
        email = resend_lib.Emails.send({
            "from": "Navigare <reports@navigare.app>",
            "to": [payload.recipient_email],
            "subject": f"Your store this week — ${payload.total_revenue:,.0f} revenue, {alert_count} alert{'s' if alert_count != 1 else ''}",
            "html": html_content,
        })
        return {"status": "sent", "email_id": email.get("id")}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send email")
