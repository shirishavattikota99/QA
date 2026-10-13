"""Transactions knowledge pack: domain guide + verified question -> query examples.

Tokens: see app/domains/common.py. To teach more, append to EXAMPLES.
"""
import re

GUIDE = """TRANSACTIONS DOMAIN GUIDE (applies to every question about deposits, withdrawals, bets, wins, payments)

The transactions collection holds every money event, one document each.
Key fields: playerId -> players._id, timestamp (event time), source, type, status, amountType, amount,
baseCurrencyAmount, paymentGatewayId -> paymentGateways._id, gameId, affiliateId, affiliateChannelId,
isFtd, isQftd.
- source: Payment, Game, Admin, Affiliate, Kiosk, Automate, Coupon, Self, Sports
- type: Deposit, Withdraw, Credit, Debit, Bet, Win, Rollback
- status: Pending, Failed, Rejected, Cancelled, Success, Initiated, Refunded, Chargeback
- amountType: Real, Bonus, Real_Bonus

Definitions
- Deposit = source "Payment", type "Deposit", status "Success".
- Withdrawal = source "Payment", type "Withdraw", status "Success".
  (Use another status only when the question names it: failed, pending, rejected, refunded, chargeback.)
- Net deposits = successful deposits minus successful withdrawals.
- Game activity: source "Game"; a game played = type "Bet"; wins = type "Win". Never use the games collection for counts.
- GGR (gross gaming revenue) = real-money bets minus real-money wins (source "Game", amountType "Real").
- Unique players = {"$addToSet": "$playerId"} then {"$size": ...}. Average per player = total / unique players.
- Use "amount" for money unless the question asks for base currency (then baseCurrencyAmount).
- Time filter field is transactions.timestamp; inclusive start, exclusive end.

Rules and pitfalls
- Put the $match (source/type/status/dates) FIRST, group next, and only then $lookup names (after $group / $limit).
- For "who / which player" questions: group by playerId, $lookup players, return the name (first + last name, else username).
- For payment method questions: group by paymentGatewayId and $lookup paymentGateways (field name).
- Do not assume every transaction question is about deposits; read the wording (withdraw, bet, win, refund, chargeback ...).
- Round money in the output with {"$round": [value, 2]} when it is a computed average or ratio."""

EXAMPLES = [
    {
        "q": "What is the total successful deposit amount this month and how many players deposited?",
        "keywords": ["total deposit", "deposit amount", "deposited", "how many players deposited", "this month", "today", "this week"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Deposit", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_month_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": None, "totalDeposits": {"$sum": "$amount"}, "deposits": {"$sum": 1}, "players": {"$addToSet": "$playerId"}}},
  {"$project": {"_id": 0, "totalDeposits": 1, "deposits": 1, "uniqueDepositors": {"$size": "$players"}}}
])""",
    },
    {
        "q": "Show deposits, withdrawals and net deposits for each month this year.",
        "keywords": ["net deposit", "monthly", "by month", "per month", "trend", "deposits and withdrawals", "cash flow"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": {"$in": ["Deposit", "Withdraw"]}, "status": "Success",
              "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
              "deposits": {"$sum": {"$cond": [{"$eq": ["$type", "Deposit"]}, "$amount", 0]}},
              "withdrawals": {"$sum": {"$cond": [{"$eq": ["$type", "Withdraw"]}, "$amount", 0]}}}},
  {"$project": {"_id": 0, "month": "$_id", "deposits": 1, "withdrawals": 1,
                "netDeposits": {"$subtract": ["$deposits", "$withdrawals"]}}},
  {"$sort": {"month": 1}}
])""",
    },
    {
        "q": "Who are the top 5 depositors this year, with their deposit totals and withdrawal counts?",
        "keywords": ["top depositors", "highest depositor", "who deposited", "which player", "player name", "top players", "biggest"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Deposit", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$playerId", "totalDeposits": {"$sum": "$amount"}}},
  {"$sort": {"totalDeposits": -1}},
  {"$limit": 5},
  @PLAYER_LOOKUP@,
  @PLAYER_UNWIND@,
  {"$lookup": {"from": "transactions", "let": {"pid": "$_id"},
               "pipeline": [{"$match": {"$expr": {"$eq": ["$playerId", "$$pid"]}, "source": "Payment", "type": "Withdraw",
                                        "status": "Success",
                                        "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
                            {"$count": "n"}],
               "as": "w"}},
  {"$project": {"_id": 0, "playerName": @PLAYER_NAME@, "totalDeposits": 1,
                "withdrawalCount": {"$ifNull": [{"$arrayElemAt": ["$w.n", 0]}, 0]}}}
])""",
    },
    {
        "q": "What share of deposit attempts succeeded, failed or were rejected last month?",
        "keywords": ["status", "failed", "rejected", "pending", "success rate", "attempts", "cancelled", "refunded", "chargeback"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Deposit",
              "timestamp": {"$gte": ISODate("<last_month_start>"), "$lt": ISODate("<this_month_start>")}}},
  {"$group": {"_id": "$status", "transactions": {"$sum": 1}, "amount": {"$sum": "$amount"}}},
  {"$sort": {"transactions": -1}},
  {"$project": {"_id": 0, "status": "$_id", "transactions": 1, "amount": 1}}
])""",
    },
    {
        "q": "Which payment gateways were used most for successful deposits this month?",
        "keywords": ["payment gateway", "gateway", "payment method", "paid through", "processor", "payment type"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Deposit", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_month_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$paymentGatewayId", "deposits": {"$sum": 1}, "amount": {"$sum": "$amount"}}},
  {"$sort": {"amount": -1}},
  {"$limit": 10},
  {"$lookup": {"from": "paymentGateways", "localField": "_id", "foreignField": "_id", "as": "gw"}},
  {"$unwind": {"path": "$gw", "preserveNullAndEmptyArrays": True}},
  {"$project": {"_id": 0, "gateway": {"$ifNull": ["$gw.name", "Unknown"]}, "deposits": 1, "amount": 1}}
])""",
    },
    {
        "q": "What were the total real-money bets, wins and GGR last month?",
        "keywords": ["ggr", "gross gaming", "bets", "wins", "wagered", "turnover", "game revenue", "gaming revenue"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Game", "type": {"$in": ["Bet", "Win"]}, "amountType": "Real",
              "timestamp": {"$gte": ISODate("<last_month_start>"), "$lt": ISODate("<this_month_start>")}}},
  {"$group": {"_id": None,
              "totalBets": {"$sum": {"$cond": [{"$eq": ["$type", "Bet"]}, "$amount", 0]}},
              "totalWins": {"$sum": {"$cond": [{"$eq": ["$type", "Win"]}, "$amount", 0]}},
              "bets": {"$sum": {"$cond": [{"$eq": ["$type", "Bet"]}, 1, 0]}}}},
  {"$project": {"_id": 0, "totalBets": 1, "totalWins": 1, "bets": 1, "ggr": {"$subtract": ["$totalBets", "$totalWins"]}}}
])""",
    },
    {
        "q": "How many withdrawals were rejected or failed this month and for how much?",
        "keywords": ["withdraw", "withdrawal", "withdrawals", "cashout", "payout"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Withdraw", "status": {"$in": ["Rejected", "Failed"]},
              "timestamp": {"$gte": ISODate("<this_month_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$status", "withdrawals": {"$sum": 1}, "amount": {"$sum": "$amount"}}},
  {"$project": {"_id": 0, "status": "$_id", "withdrawals": 1, "amount": 1}}
])""",
    },
    {
        "q": "What is the average successful deposit per depositing player this year?",
        "keywords": ["average", "avg", "per player", "mean", "typical"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Deposit", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$playerId", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
  {"$group": {"_id": None, "depositors": {"$sum": 1}, "avgTotalPerPlayer": {"$avg": "$total"}, "avgDepositSize": {"$avg": {"$divide": ["$total", "$count"]}}}},
  {"$project": {"_id": 0, "depositors": 1, "avgTotalPerPlayer": {"$round": ["$avgTotalPerPlayer", 2]}, "avgDepositSize": {"$round": ["$avgDepositSize", 2]}}}
])""",
    },
]

TRIGGER = re.compile(
    r"transaction|deposit|withdraw|\bbets?\b|\bbetting\b|wager|\bwins?\b|winnings|\bggr\b|\bngr\b|"
    r"payment|gateway|refund|chargeback|rollback|net deposit|turnover|\bftds?\b|first[- ]time deposit",
    re.IGNORECASE,
)