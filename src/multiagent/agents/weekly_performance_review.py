"""Every Monday: review last week's TikTok numbers, surface what worked, and
suggest what to do more of. Logs the snapshot to a Sheet."""

from __future__ import annotations

from datetime import date

from ..core import Agent, AgentResult, Context, register


@register
class WeeklyPerformanceReview(Agent):
    name = "weekly_performance_review"
    description = "Weekly performance review"

    def run(self, ctx: Context) -> AgentResult:
        posts = ctx.tiktok.my_recent_posts(days=7)
        if not posts:
            return AgentResult(
                title="📊 Weekly performance", body="No posts in the last 7 days."
            )

        total_views = sum(p["views"] for p in posts)
        total_eng = sum(p["likes"] + p["comments"] + p["shares"] for p in posts)
        best = max(posts, key=lambda p: p["views"])

        system = (
            "You are a data-literate content coach for a "
            f"{ctx.business.niche} creator.\n{ctx.business.as_prompt()}\n"
            "Be concrete: name patterns, not platitudes."
        )
        prompt = (
            "Here is last week's TikTok performance:\n"
            + "\n".join(
                f"- {p['caption']}: {p['views']:,} views, {p['likes']:,} likes, "
                f"{p['comments']:,} comments, {p['shares']:,} shares"
                for p in posts
            )
            + f"\n\nTotals: {total_views:,} views, {total_eng:,} engagements across "
            f"{len(posts)} posts.\n\n"
            "Give me: (1) what worked and why, (2) what underperformed, "
            "(3) 3 specific things to do MORE of next week, (4) one experiment to try."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=1800)

        # One row per week for the tracking sheet.
        row = [
            str(date.today()),
            len(posts),
            total_views,
            total_eng,
            best["caption"],
            best["views"],
        ]
        return AgentResult(
            title="📊 Weekly performance review",
            body=body,
            data={
                "rows": [row],
                "sheet_id": ctx.integrations.sheets.env("PERFORMANCE_SHEET_ID", "") or "",
                "tab": "Weekly",
            },
        )
