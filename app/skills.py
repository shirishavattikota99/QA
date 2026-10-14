from typing import TypedDict


class Skill(TypedDict):
    """A skill that can be progressively disclosed to the agent."""
    name: str  # unique name of the skill
    description: str
    content: str


# ======= Complete skills for Casino CRM analytics ============
SKILLS: list[Skill] = [
    {
        "name": "mongodb_collection_descriptions",
        "description": "MongoDB collections overview for correct querying and interpretation",
        "content": """# Casino - MongoDB collection descriptions & business rules

## COLLECTION DESCRIPTIONS:

## players
- Stores player profile, authentication details, KYC status, wallet snapshot, affiliate data, loyalty progress, and lifetime activity metrics.
- Acts as the primary source of truth for player identity and high-level financial/behavioral summaries.
- Contains only the latest snapshot (current balances and aggregated lifetime stats), not time-series data.
- For time-based gameplay, deposit, or withdrawal activity, refer to the `transactions` collection.
- Player registration date is stored in `players.createdAt`.
- Affiliate-attributed registrations are identified by `players.affiliateId`.
- The specific marketing channel that generated a signup is stored in `players.affiliateChannelId`.

## transactions
- Stores all financial and gameplay activity for players.
- Includes deposits, withdrawals, bets, wins, rollbacks, and admin adjustments.
- Acts as the single source of truth for time-series and event-level data.
- Each document represents a single transaction/event with status, type, source, amountType, amount and balance snapshots.
- Use this collection for all time-based analysis (e.g., gameplay activity(bets,wins,rollbacks), deposits, withdrawals, revenue, retention).
- Game activity, financial reports, and player behavior over time MUST be derived from this collection, not from `players`.

## games
- Stores static metadata about games, including names, providers, categories, and configuration details.
- Does NOT contain gameplay or transactional activity.
- Used for game lookup, filtering, and enrichment of gameplay data from `transactions`.
- Related transactions will have `source = "Game"` referencing gameplay activity in transactions collection.

## sessions
- Tracks player/affiliate login sessions, including login/logout times, activity status, and device/network details.
- Used for monitoring player activity, session duration, and online presence.
- Not related to gameplay or financial transactions.

## affiliates
- Stores affiliate partner information, including profile details, account status, and marketing configurations.
- Contains referral hierarchy (parent/child relationships) and commission settings.
- Used to track and attribute player acquisition, traffic sources, and affiliate-driven activity.

## affiliateClicks
- Tracks clicks from affiliate links and may include click-to-registration flags.
- Use this only for click/campaign-funnel analysis.
- Do not use this as the primary source for player registration lists when `players.affiliateId` is available.

## affiliateChannels
- Tracks performance and configuration of individual marketing channels under affiliate partners.
- Contains deal structures (CPA, Revenue Sharing, Hybrid), commission rules, and qualification conditions.
- Stores aggregated metrics such as signups, deposits, FTDs, withdrawals, and total earnings for each channel.
- Used for attribution, performance analysis, and affiliate payout calculations.

## categories
- Stores game categories (e.g., slots, table, live).
- Used to classify and filter games.

## providers
- Stores game providers/vendors.
- Used to group and filter games by provider.

## paymentGateways
- Stores the payment methods / gateways players can use (name, type, status, limits).
- "Active payment methods" = paymentGateways whose status/active field is the ACTIVE value (use the values listed under "Observed values", never guess).
- Never use it for payment counts or amounts; those live in `transactions`.

## KYC
- Player KYC state lives on `players` (a kyc status field, see schema). If a collection with "kyc" in its name exists, it holds the verification records/documents.
- "KYC pending / approved / rejected / not submitted" = filter that status field using ONLY the observed values.
- Return only username, email, createdAt, kyc status. Never return KYC documents, bank or ID details.

## coupons
- Collections with "coupon" in the name hold coupon definitions (code, status, validity, value).
- Coupon amounts credited to players are `transactions` with source = "Coupon".

## sports
- Collections with "sport" in the name hold sports / event / market metadata.
- Sports betting activity is `transactions` with source = "Sports" (type Bet / Win / Rollback).

## QUESTION CHEAT SHEET
- Active games -> `games`, filter by its status/active field, then $count.
- Games or providers lists -> `games` / `providers`; games per provider = group games by its provider reference, $lookup providers for the name.
- Active payment methods -> `paymentGateways` filtered by active status.
- Payment method with most successful transactions -> `transactions` match source "Payment", status "Success"; $group by the payment gateway reference field in transactions with a count; $sort desc; $limit; $lookup `paymentGateways` for the name.
- Payment methods players used -> same, but count distinct players per gateway (group by gateway + player first, then group by gateway).
- KYC questions -> `players` kyc status field (or the kyc collection if it exists).
- Coupon questions -> the coupon collection (definitions) and/or `transactions` source "Coupon" (redemptions).
- Sports questions -> the sports collection (metadata) and/or `transactions` source "Sports" (bets).

## BUSINESS RULES:

## Player Registration
- Registration filtering uses `players.createdAt`.
- "Registered through affiliates" means players with `affiliateId` present and not null.
- Join `affiliates` only when affiliate details are requested.
- Join `affiliateChannels` only when channel details are requested.

## Game Activity
- Time-based gameplay must be derived from `transactions`.
- To count games played, count `transactions` where `source = "Game"` and `type = "Bet"`.
- Never use the `games` collection for gameplay counts.

### CMS (content management system)
## Collections related to CMS content management (customComponents, dynamicPages, pageContents, pageLayoutTemplates, pageLayouts)
- Stores dynamic website/app content such as pages, layouts, and reusable components.
- Used for rendering frontend UI/UX structure and managing localized or configurable content.
"""
    }
]