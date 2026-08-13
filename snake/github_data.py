"""Busca a atividade diaria do GitHub via GraphQL."""
import json
import urllib.request
from datetime import datetime, timedelta, timezone

ENDPOINT = "https://api.github.com/graphql"

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
      commitContributionsByRepository(maxRepositories:100) {
        repository { nameWithOwner }
        contributions(first:100) { nodes { occurredAt } }
      }
    }
  }
}
"""


def fetch(login, token, days=371):
    to = datetime.now(timezone.utc)
    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": login,
            "from": (to - timedelta(days=days)).isoformat(),
            "to": to.isoformat(),
        },
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=payload, headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "snake-grid",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]["user"]["contributionsCollection"]


def daily_activity(collection):
    """{'2026-08-06': {'count': 7, 'repos': {'owner/repo', ...}}}"""
    days = {}
    for week in collection["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            days[day["date"]] = {"count": day["contributionCount"], "repos": set()}
    for repo in collection["commitContributionsByRepository"]:
        name = repo["repository"]["nameWithOwner"]
        for node in repo["contributions"]["nodes"]:
            day = node["occurredAt"][:10]
            if day in days:
                days[day]["repos"].add(name)
    return days
