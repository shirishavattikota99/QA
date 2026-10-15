"""Coupons knowledge pack: domain guide + verified question -> query examples.

Tokens inside example queries: <this_year_start> <this_month_start> <last_month_start>
<last_30d_start> <today_start> <tomorrow_start> (real dates) and @PLAYER_LOOKUP@ @PLAYER_NAME@ ...
(see app/domains/common.py). To teach more, append to EXAMPLES.

TODO(verify): the repo's schema files do not describe the `coupons` collection itself, so the
field names used for coupon DEFINITIONS below (code, status, validFrom/validTill, ...) are
assumptions. Check them against your real collection (db.coupons.findOne()) and fix GUIDE and
the examples marked "# DEFINITION". The REDEMPTION side (transactions.source = "Coupon",
transactions.couponId) comes straight from the existing schema and is reliable.
"""
import re

GUIDE = """COUPONS DOMAIN GUIDE (applies to every question about coupons, promo codes, vouchers, redemptions)

Collections and how they link
- coupons: one document per coupon definition (code, status, validity, value). Use ONLY the field
  names present in the supplied schema / observed values for this collection; never invent fields.
- transactions: a coupon redemption is a transaction with source "Coupon".
  Key fields: couponId -> coupons._id, playerId -> players._id, timestamp, type, status,
  amountType, amount, baseCurrencyAmount.
- players: playerId in transactions -> players._id (username, firstName, lastName).

Definitions
- "Coupon redeemed / used / claimed" = transactions with source "Coupon" and status "Success".
  Count with {"$sum": 1}; unique players = {"$addToSet": "$playerId"} then {"$size": ...}.
- "Coupon amount / value given to players" = sum of "amount" on those transactions
  (use baseCurrencyAmount only when the question asks for base currency / EUR).
- "Redemptions per coupon" = group those transactions by couponId, then $lookup coupons for the code/name.
- Coupon credits normally have type "Credit"; do not add a type filter unless the question names one.
- Failed / rejected / pending coupon attempts: change status only when the question names it.
- "Active / expired coupons" are questions about the coupons collection (definitions): filter its
  status or validity fields using ONLY the observed values; do not read transactions for those.
- Coupons never redeemed = coupons whose _id has no transactions with source "Coupon"
  (use $lookup from transactions on couponId and keep those with an empty result).

Rules and pitfalls
- Put the $match (source "Coupon", status, dates) FIRST, group next, and only then $lookup names
  (after $group / $limit).
- Time filter field is transactions.timestamp; inclusive start, exclusive end.
- Always filter couponId with {"$exists": True, "$ne": None} before grouping by couponId.
- After $limit, $lookup coupons and use "$unwind": {"path": "$cp", "preserveNullAndEmptyArrays": True}
  so no ranked row is dropped; show a coupon code/name, falling back to the id as text.
- For "who redeemed" questions: group by playerId, $lookup players, return the player name.
- Never return passwords, emails, mobile numbers or other personal data unless explicitly asked."""

EXAMPLES = [
    {
        "q": "How many coupons were redeemed this month, how much was given out, and by how many players?",
        "keywords": ["redeemed", "redemptions", "coupon amount", "given out", "claimed", "used", "this month"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Coupon", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_month_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": None, "redemptions": {"$sum": 1}, "totalAmount": {"$sum": "$amount"}, "players": {"$addToSet": "$playerId"}}},
  {"$project": {"_id": 0, "redemptions": 1, "totalAmount": 1, "uniquePlayers": {"$size": "$players"}}}
])""",
    },
    {
        "q": "Which are the top 5 most redeemed coupons this year?",
        "keywords": ["top coupons", "most redeemed", "most used", "popular", "best coupon", "per coupon"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Coupon", "status": "Success", "couponId": {"$exists": True, "$ne": None},
              "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$couponId", "redemptions": {"$sum": 1}, "totalAmount": {"$sum": "$amount"}, "players": {"$addToSet": "$playerId"}}},
  {"$sort": {"redemptions": -1}},
  {"$limit": 5},
  {"$lookup": {"from": "coupons", "localField": "_id", "foreignField": "_id", "as": "cp"}},
  {"$unwind": {"path": "$cp", "preserveNullAndEmptyArrays": True}},
  {"$project": {"_id": 0, "coupon": {"$ifNull": ["$cp.code", {"$toString": "$_id"}]},
                "redemptions": 1, "totalAmount": 1, "uniquePlayers": {"$size": "$players"}}}
])""",
    },
    {
        "q": "Show the total coupon amount credited per month this year.",
        "keywords": ["monthly", "per month", "by month", "trend", "coupon amount per month"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Coupon", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
              "redemptions": {"$sum": 1}, "totalAmount": {"$sum": "$amount"}}},
  {"$project": {"_id": 0, "month": "$_id", "redemptions": 1, "totalAmount": 1}},
  {"$sort": {"month": 1}}
])""",
    },
    {
        "q": "Who are the top 5 players by coupon amount received this year?",
        "keywords": ["who redeemed", "which player", "top players", "player name", "most coupons", "received coupons"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Coupon", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$playerId", "couponAmount": {"$sum": "$amount"}, "redemptions": {"$sum": 1}}},
  {"$sort": {"couponAmount": -1}},
  {"$limit": 5},
  @PLAYER_LOOKUP@,
  @PLAYER_UNWIND@,
  {"$project": {"_id": 0, "playerName": @PLAYER_NAME@, "couponAmount": 1, "redemptions": 1}}
])""",
    },
    {
        "q": "How many coupon redemptions failed or were rejected last month?",
        "keywords": ["failed", "rejected", "pending", "cancelled", "unsuccessful", "status"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Coupon",
              "timestamp": {"$gte": ISODate("<last_month_start>"), "$lt": ISODate("<this_month_start>")}}},
  {"$group": {"_id": "$status", "transactions": {"$sum": 1}, "amount": {"$sum": "$amount"}}},
  {"$sort": {"transactions": -1}},
  {"$project": {"_id": 0, "status": "$_id", "transactions": 1, "amount": 1}}
])""",
    },
    {
        "q": "What is the average coupon amount per redemption, and per player, this year?",
        "keywords": ["average", "avg", "per redemption", "per player", "mean", "typical"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Coupon", "status": "Success",
              "timestamp": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$playerId", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
  {"$group": {"_id": None, "players": {"$sum": 1}, "redemptions": {"$sum": "$count"},
              "avgPerPlayer": {"$avg": "$total"}, "totalAmount": {"$sum": "$total"}}},
  {"$project": {"_id": 0, "players": 1, "redemptions": 1,
                "avgPerPlayer": {"$round": ["$avgPerPlayer", 2]},
                "avgPerRedemption": {"$round": [{"$divide": ["$totalAmount", {"$max": ["$redemptions", 1]}]}, 2]}}}
])""",
    },
    {
        "q": "Which coupons have never been redeemed?",
        "keywords": ["never redeemed", "not redeemed", "unused", "no redemptions", "zero redemptions"],
        # DEFINITION: reads the coupons collection; "code" is an assumed field (see module TODO).
        "query": """db.coupons.aggregate([
  {"$lookup": {"from": "transactions", "let": {"cid": "$_id"},
               "pipeline": [{"$match": {"$expr": {"$eq": ["$couponId", "$$cid"]}, "source": "Coupon", "status": "Success"}},
                            {"$limit": 1}],
               "as": "used"}},
  {"$match": {"used": {"$size": 0}}},
  {"$limit": 20},
  {"$project": {"_id": 0, "coupon": {"$ifNull": ["$code", {"$toString": "$_id"}]}}}
])""",
    },
    {
        "q": "How many coupons do we have by status?",
        "keywords": ["how many coupons", "number of coupons", "count of coupons", "by status", "active coupons", "expired", "inactive"],
        # DEFINITION: "status" is an assumed field (see module TODO); check observed values.
        "query": """db.coupons.aggregate([
  {"$group": {"_id": "$status", "coupons": {"$sum": 1}}},
  {"$sort": {"coupons": -1}},
  {"$project": {"_id": 0, "status": "$_id", "coupons": 1}}
])""",
    },
    {
        "q": "Match the coupon code SUMMER to its redemptions in the last 30 days.",
        "keywords": ["coupon code", "code", "named", "specific coupon", "promo code", "voucher"],
        # DEFINITION: filters coupons.code with a case-insensitive regex (assumed field).
        "query": """db.coupons.aggregate([
  {"$match": {"code": {"$regex": "SUMMER", "$options": "i"}}},
  {"$lookup": {"from": "transactions", "let": {"cid": "$_id"},
               "pipeline": [{"$match": {"$expr": {"$eq": ["$couponId", "$$cid"]}, "source": "Coupon", "status": "Success",
                                        "timestamp": {"$gte": ISODate("<last_30d_start>"), "$lt": ISODate("<tomorrow_start>")}}},
                            {"$group": {"_id": None, "redemptions": {"$sum": 1}, "amount": {"$sum": "$amount"}}}],
               "as": "r"}},
  {"$limit": 20},
  {"$project": {"_id": 0, "coupon": "$code",
                "redemptions": {"$ifNull": [{"$arrayElemAt": ["$r.redemptions", 0]}, 0]},
                "amount": {"$ifNull": [{"$arrayElemAt": ["$r.amount", 0]}, 0]}}}
])""",
    },
]

TRIGGER = re.compile(r"coupon|promo code|promocode|voucher|redeem|redemption", re.IGNORECASE)
