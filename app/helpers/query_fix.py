"""Repair small syntax slips in generated MongoDB queries before they are run.

The query tool (langchain-mongodb) turns the text `db.x.aggregate([...])` into Python with a
regex-based parser. That parser rejects a few things the LLM writes all the time:

  * field paths into a grouped _id, e.g.  "$_id.countryId"   (the usual way to read a compound _id)
  * JSON-style literals true / false / null                  (the parser only knows True / False / None)
  * {"$oid": "..."}                                          (kept as a plain dict, so ids never match)

Each of these makes the whole query fail with "Failed to parse aggregation pipeline" even though
the query is valid MongoDB. fix_query() rewrites them:

    "$_id.countryId"  ->  "$\\u005fid.countryId"   (Python reads \\u005f inside a string as "_")
    true / false / null  ->  True / False / None    (only outside quoted strings)
    {"$oid": "<24 hex>"} ->  ObjectId("<24 hex>")

Use it right before the query runs:
    call["args"]["query"] = fix_query(call["args"].get("query", ""))
and undo the \\u005f spelling when you SHOW the query to a person:
    shown = query.replace("\\\\u005fid", "_id")
"""
import re

# One pass over the text: a quoted string is captured whole (so its content is never mistaken for
# code); anything else is matched as a bare word.
_TOKEN = re.compile(
    r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''  # 1: a quoted string
    r"|\b(true|false|null)\b"                      # 2: a JSON-style literal outside strings
)
_LITERALS = {"true": "True", "false": "False", "null": "None"}
_ID_PATH = re.compile(r"\$_id(?=\.)")              # "$_id.field" (not a bare "$_id")
_OID = re.compile(r"""\{\s*["']\$oid["']\s*:\s*["']([0-9a-fA-F]{24})["']\s*\}""")


def _fix_token(match: re.Match) -> str:
    text = match.group(1)
    if text is None:  # a bare true / false / null
        return _LITERALS[match.group(2)]
    return _ID_PATH.sub(r"$\\u005fid", text)


def fix_query(query: str) -> str:
    """Return `query` with the parser-hostile spellings above rewritten. Safe to call twice."""
    if not query:
        return query
    query = _OID.sub(r'ObjectId("\1")', query)
    return _TOKEN.sub(_fix_token, query)