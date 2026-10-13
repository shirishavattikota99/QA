"""Affiliates knowledge pack: domain guide + verified question -> query examples.

Tokens inside example queries: <this_year_start> <this_month_start> <last_month_start>
<last_30d_start> <today_start> <tomorrow_start> (real dates) and @NAME_AFF@ @AFF_LOOKUP@ ...
(see app/domains/common.py). To teach more, append to EXAMPLES.
"""
import re

GUIDE = """AFFILIATE DOMAIN GUIDE (applies to every question about affiliates, referrals, channels, signups)

Collections and how they link
- affiliates: one document per affiliate partner. Display name = companyName, else username.
  Fields: username, email, firstName, lastName, status (Pending|Active|Inactive),
  access (Normal|Manager), marketingVia (Digital|Media|Mail|Advertisements), trafficSource,
  countryId -> countries._id (countries.name), balance (payable amount, >= 0), createdAt,
  postbackUrls.registerUrl / postbackUrls.qFtdUrl.
- affiliateChannels: tracking channels owned by an affiliate. affiliateId -> affiliates._id.
  Fields: name, endpoint, status (Pending|Active|Inactive), dealType (CPA|RevenueSharing|Hybrid),
  conditionType (Normal|QCPA), dealAmount, dealPercentage, adminFeePercent,
  baselineDepositAmount, baselineDepositCount, baselineWagerAmount.
  Ready-made counters: signupCount, depositCount, withdrawCount, ftdCount, qFtdCount,
  totalDepositAmount, totalQualifiedDepositAmount, totalWithdrawAmount, totalEarnings.
- players: affiliateId -> affiliates._id, affiliateChannelId -> affiliateChannels._id,
  createdAt (registration date), totalDepositAmount, totalDepositCount, lastDepositAt.
- transactions: affiliateId, affiliateChannelId, isFtd, isQftd, plus source/type/status/amount/timestamp.

Definitions
- "registered / referred / signed up through an affiliate" = a players document whose affiliateId
  exists and is not null. The registration date is players.createdAt.
- "registrations (or players) per affiliate" = group those players by players.affiliateId and count.
- "per channel" = group players by players.affiliateChannelId and look up affiliateChannels.name.
- FTD = first time deposit (transactions.isFtd = True); QFTD = qualified FTD (transactions.isQftd = True).
  Channel-level totals are already stored in affiliateChannels.ftdCount / qFtdCount.
- Affiliate earnings / commission / payout = affiliateChannels.totalEarnings (sum it per affiliate).
  "Balance" = affiliates.balance.
- Deposits made by an affiliate's players: players.totalDepositAmount grouped by players.affiliateId
  (lifetime), or successful Payment/Deposit transactions in a period (see the examples).
- "Active affiliate" = affiliates.status "Active". Counting affiliates must read the affiliates
  collection (affiliates with zero players still count).
- Country of an affiliate = affiliates.countryId looked up in countries (name).

Rules and pitfalls
- Never use players.affiliateQueryParams or wyntaAffiliateClickId as the affiliate identifier, and
  do not use affiliateClicks as the source of registrations.
- Before grouping players by affiliateId, ALWAYS $match {"affiliateId": {"$exists": True, "$ne": None}}.
- After $limit, $lookup affiliates and use "$unwind": {"path": "$aff", "preserveNullAndEmptyArrays": True}
  so no ranked row is dropped, and show a name (companyName, else username, else the id as text), never only an id.
- Apply a date filter only when the question gives a period; use players.createdAt for registrations,
  transactions.timestamp for deposits, affiliates.createdAt for when an affiliate joined.
- Match a name the user typed with a case-insensitive $regex on companyName OR username.
- Never return password, email, mobile or postbackUrls unless the user explicitly asks for them.
- Use only fields listed above or present in the supplied schema; never invent fields."""

EXAMPLES = [
    {
        "q": "List the top 5 affiliates by registered player count.",
        "keywords": ["top", "most", "highest", "registered", "registrations", "signups", "referred", "players"],
        "query": """db.players.aggregate([
  {"$match": {"affiliateId": {"$exists": True, "$ne": None}}},
  {"$group": {"_id": "$affiliateId", "registeredPlayers": {"$sum": 1}}},
  {"$sort": {"registeredPlayers": -1}},
  {"$limit": 5},
  @AFF_LOOKUP@,
  @AFF_UNWIND@,
  {"$project": {"_id": 0, "affiliateName": @NAME_AFF@, "registeredPlayers": 1}}
])""",
    },
    {
        "q": "How many players did each affiliate register last month?",
        "keywords": ["each", "per affiliate", "last month", "this month", "registered", "registrations", "period"],
        "query": """db.players.aggregate([
  {"$match": {"affiliateId": {"$exists": True, "$ne": None},
              "createdAt": {"$gte": ISODate("<last_month_start>"), "$lt": ISODate("<this_month_start>")}}},
  {"$group": {"_id": "$affiliateId", "registeredPlayers": {"$sum": 1}}},
  {"$sort": {"registeredPlayers": -1}},
  @AFF_LOOKUP@,
  @AFF_UNWIND@,
  {"$project": {"_id": 0, "affiliateName": @NAME_AFF@, "registeredPlayers": 1}}
])""",
    },
    {
        "q": "What percentage of players registered through affiliates?",
        "keywords": ["percentage", "percent", "share", "proportion", "ratio", "out of all players"],
        "query": """db.players.aggregate([
  {"$group": {"_id": None, "totalPlayers": {"$sum": 1},
              "viaAffiliates": {"$sum": {"$cond": [{"$ne": [{"$ifNull": ["$affiliateId", None]}, None]}, 1, 0]}}}},
  {"$project": {"_id": 0, "totalPlayers": 1, "viaAffiliates": 1,
                "percentage": {"$round": [{"$multiply": [{"$divide": ["$viaAffiliates", {"$max": ["$totalPlayers", 1]}]}, 100]}, 2]}}}
])""",
    },
    {
        "q": "How many affiliates do we have by status?",
        "keywords": ["how many affiliates", "number of affiliates", "count of affiliates", "by status", "active affiliates", "inactive", "pending"],
        "query": """db.affiliates.aggregate([
  {"$group": {"_id": "$status", "affiliates": {"$sum": 1}}},
  {"$sort": {"affiliates": -1}},
  {"$project": {"_id": 0, "status": "$_id", "affiliates": 1}}
])""",
    },
    {
        "q": "List the active affiliates with their company name and join date.",
        "keywords": ["list", "show", "active affiliates", "all affiliates", "joined", "join date", "newest", "latest"],
        "query": """db.affiliates.aggregate([
  {"$match": {"status": "Active"}},
  {"$sort": {"createdAt": -1}},
  {"$limit": 20},
  {"$project": {"_id": 0, "affiliateName": @NAME_DIRECT@, "username": 1, "status": 1, "createdAt": 1}}
])""",
    },
    {
        "q": "How many new affiliates joined this year?",
        "keywords": ["new affiliates", "joined", "signed up as", "onboarded", "this year", "this month", "created"],
        "query": """db.affiliates.aggregate([
  {"$match": {"createdAt": {"$gte": ISODate("<this_year_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$count": "newAffiliates"}
])""",
    },
    {
        "q": "Which affiliates have not registered any players?",
        "keywords": ["no players", "not registered", "without players", "zero registrations", "no registrations", "inactive affiliates", "never"],
        "query": """db.affiliates.aggregate([
  {"$lookup": {"from": "players", "let": {"a": "$_id"},
               "pipeline": [{"$match": {"$expr": {"$eq": ["$affiliateId", "$$a"]}}}, {"$limit": 1}, {"$project": {"_id": 1}}],
               "as": "p"}},
  {"$match": {"p": {"$size": 0}}},
  {"$limit": 50},
  {"$project": {"_id": 0, "affiliateName": @NAME_DIRECT@, "status": 1, "createdAt": 1}}
])""",
    },
    {
        "q": "How many affiliate channels do we have for each deal type?",
        "keywords": ["deal type", "cpa", "revenue share", "revenuesharing", "hybrid", "qcpa", "condition", "deal"],
        "query": """db.affiliateChannels.aggregate([
  {"$group": {"_id": "$dealType", "channels": {"$sum": 1}}},
  {"$sort": {"channels": -1}},
  {"$project": {"_id": 0, "dealType": "$_id", "channels": 1}}
])""",
    },
    {
        "q": "Which 5 affiliate channels earned the most, and which affiliate owns each?",
        "keywords": ["channel", "channels", "earned", "earnings", "commission", "payout", "revenue", "most profitable"],
        "query": """db.affiliateChannels.aggregate([
  {"$sort": {"totalEarnings": -1}},
  {"$limit": 5},
  {"$lookup": {"from": "affiliates", "localField": "affiliateId", "foreignField": "_id", "as": "aff"}},
  {"$unwind": {"path": "$aff", "preserveNullAndEmptyArrays": True}},
  {"$project": {"_id": 0, "channelName": "$name", "affiliateName": @NAME_AFF@, "totalEarnings": 1, "signupCount": 1}}
])""",
    },
    {
        "q": "Show each affiliate's total signups, FTDs, deposits and earnings.",
        "keywords": ["performance", "summary", "overview", "ftd", "qftd", "signups", "deposits", "earnings", "report", "each affiliate"],
        "query": """db.affiliateChannels.aggregate([
  {"$group": {"_id": "$affiliateId", "signups": {"$sum": "$signupCount"}, "ftds": {"$sum": "$ftdCount"},
              "qualifiedFtds": {"$sum": "$qFtdCount"}, "deposits": {"$sum": "$totalDepositAmount"},
              "earnings": {"$sum": "$totalEarnings"}}},
  {"$sort": {"earnings": -1}},
  {"$limit": 20},
  @AFF_LOOKUP@,
  @AFF_UNWIND@,
  {"$project": {"_id": 0, "affiliateName": @NAME_AFF@, "signups": 1, "ftds": 1, "qualifiedFtds": 1, "deposits": 1, "earnings": 1}}
])""",
    },
    {
        "q": "Which affiliates' players deposited the most in total?",
        "keywords": ["players deposited", "deposit", "deposits", "deposited", "lifetime", "revenue from", "value"],
        "query": """db.players.aggregate([
  {"$match": {"affiliateId": {"$exists": True, "$ne": None}}},
  {"$group": {"_id": "$affiliateId", "totalDeposits": {"$sum": "$totalDepositAmount"}, "players": {"$sum": 1}}},
  {"$sort": {"totalDeposits": -1}},
  {"$limit": 5},
  @AFF_LOOKUP@,
  @AFF_UNWIND@,
  {"$project": {"_id": 0, "affiliateName": @NAME_AFF@, "players": 1, "totalDeposits": 1}}
])""",
    },
    {
        "q": "How many first-time deposits (FTDs) came from each affiliate this month?",
        "keywords": ["ftd", "first time deposit", "first deposit", "qftd", "qualified"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Deposit", "status": "Success", "isFtd": True,
              "affiliateId": {"$exists": True, "$ne": None},
              "timestamp": {"$gte": ISODate("<this_month_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$affiliateId", "ftdCount": {"$sum": 1}, "ftdAmount": {"$sum": "$amount"}}},
  {"$sort": {"ftdCount": -1}},
  {"$limit": 20},
  @AFF_LOOKUP@,
  @AFF_UNWIND@,
  {"$project": {"_id": 0, "affiliateName": @NAME_AFF@, "ftdCount": 1, "ftdAmount": 1}}
])""",
    },
    {
        "q": "Total successful deposit amount from affiliate-referred players in the last 30 days, per affiliate.",
        "keywords": ["successful deposit", "deposit amount", "last 30 days", "last 7 days", "this week", "per affiliate"],
        "query": """db.transactions.aggregate([
  {"$match": {"source": "Payment", "type": "Deposit", "status": "Success",
              "affiliateId": {"$exists": True, "$ne": None},
              "timestamp": {"$gte": ISODate("<last_30d_start>"), "$lt": ISODate("<tomorrow_start>")}}},
  {"$group": {"_id": "$affiliateId", "depositAmount": {"$sum": "$amount"}, "deposits": {"$sum": 1}}},
  {"$sort": {"depositAmount": -1}},
  {"$limit": 20},
  @AFF_LOOKUP@,
  @AFF_UNWIND@,
  {"$project": {"_id": 0, "affiliateName": @NAME_AFF@, "deposits": 1, "depositAmount": 1}}
])""",
    },
    {
        "q": "Show monthly registrations for the affiliate named priva.",
        "keywords": ["monthly", "trend", "by month", "over time", "per month", "named", "specific affiliate", "registrations for"],
        "query": """db.players.aggregate([
  {"$match": {"affiliateId": {"$exists": True, "$ne": None}}},
  {"$lookup": {"from": "affiliates", "localField": "affiliateId", "foreignField": "_id", "as": "aff"}},
  {"$unwind": "$aff"},
  {"$match": {"$or": [{"aff.companyName": {"$regex": "priva", "$options": "i"}},
                      {"aff.username": {"$regex": "priva", "$options": "i"}}]}},
  {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}}, "registrations": {"$sum": 1}}},
  {"$sort": {"_id": 1}},
  {"$project": {"_id": 0, "month": "$_id", "registrations": 1}}
])""",
    },
    {
        "q": "Which marketing channels or traffic sources do our affiliates use most?",
        "keywords": ["marketing", "marketingvia", "traffic source", "trafficsource", "digital", "media", "mail", "advertisements"],
        "query": """db.affiliates.aggregate([
  {"$group": {"_id": "$marketingVia", "affiliates": {"$sum": 1}}},
  {"$sort": {"affiliates": -1}},
  {"$project": {"_id": 0, "marketingVia": "$_id", "affiliates": 1}}
])""",
    },
    {
        "q": "How many affiliates are there in each country?",
        "keywords": ["country", "countries", "region", "geography", "where"],
        "query": """db.affiliates.aggregate([
  {"$group": {"_id": "$countryId", "affiliates": {"$sum": 1}}},
  {"$sort": {"affiliates": -1}},
  {"$lookup": {"from": "countries", "localField": "_id", "foreignField": "_id", "as": "country"}},
  {"$unwind": {"path": "$country", "preserveNullAndEmptyArrays": True}},
  {"$project": {"_id": 0, "country": {"$ifNull": ["$country.name", "Unknown"]}, "affiliates": 1}}
])""",
    },
    {
        "q": "Which 5 affiliates have the highest balance?",
        "keywords": ["balance", "payable", "owed", "unpaid", "pending payout"],
        "query": """db.affiliates.aggregate([
  {"$match": {"balance": {"$gt": 0}}},
  {"$sort": {"balance": -1}},
  {"$limit": 5},
  {"$project": {"_id": 0, "affiliateName": @NAME_DIRECT@, "balance": 1}}
])""",
    },
    {
        "q": "Which affiliate channels brought the most registered players?",
        "keywords": ["channel", "channels", "campaign", "link", "endpoint", "which channel"],
        "query": """db.players.aggregate([
  {"$match": {"affiliateChannelId": {"$exists": True, "$ne": None}}},
  {"$group": {"_id": "$affiliateChannelId", "registeredPlayers": {"$sum": 1}}},
  {"$sort": {"registeredPlayers": -1}},
  {"$limit": 5},
  {"$lookup": {"from": "affiliateChannels", "localField": "_id", "foreignField": "_id", "as": "ch"}},
  {"$unwind": {"path": "$ch", "preserveNullAndEmptyArrays": True}},
  {"$project": {"_id": 0, "channelName": {"$ifNull": ["$ch.name", {"$toString": "$_id"}]}, "registeredPlayers": 1}}
])""",
    },
    {
        "q": "List the channels of the affiliate privaaff with their deal type and status.",
        "keywords": ["channels of", "channel details", "deal", "owned by", "belongs to", "named", "affiliate's channels"],
        "query": """db.affiliateChannels.aggregate([
  {"$lookup": {"from": "affiliates", "localField": "affiliateId", "foreignField": "_id", "as": "aff"}},
  {"$unwind": "$aff"},
  {"$match": {"$or": [{"aff.companyName": {"$regex": "privaaff", "$options": "i"}},
                      {"aff.username": {"$regex": "privaaff", "$options": "i"}}]}},
  {"$limit": 50},
  {"$project": {"_id": 0, "channelName": "$name", "status": 1, "dealType": 1, "dealAmount": 1,
                "dealPercentage": 1, "signupCount": 1, "totalEarnings": 1}}
])""",
    },
]

TRIGGER = re.compile(
    r"affiliat|referr|referral|\bchannels?\b|\bq?ftds?\b|first[- ]time deposit|postback|\bcpa\b|"
    r"revenue ?shar|commission|traffic source|marketing ?via|"
    r"(?:signed up|registered|registrations?|signups?) (?:through|via|from|by)",
    re.IGNORECASE,
)