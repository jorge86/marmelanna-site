#!/usr/bin/env python3
"""
Ημερήσια σύνοψη επισκεψιμότητας από το Cloudflare Web Analytics.

Τρέχει από GitHub Actions (.github/workflows/analytics-digest.yml) και γράφει
σχόλιο σε ένα μόνιμο issue του repo — το GitHub στέλνει το email.

Γιατί σχόλιο σε ένα issue και όχι νέο issue κάθε μέρα: 365 issues τον χρόνο
είναι σκουπίδια. Ένα issue με ιστορικό σχολίων διαβάζεται σαν ημερολόγιο.

Μεταβλητές περιβάλλοντος:
  CF_API_TOKEN, CF_ACCOUNT_ID   από τα GitHub secrets
  GITHUB_TOKEN, GITHUB_REPOSITORY  δίνονται αυτόματα από το Actions
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

SITE_TAG    = "cf34922e2ffb4b639aced62b6f5599d9"   # ίδιο με το beacon· δημόσιο
ISSUE_TITLE = "Επισκεψιμότητα — ημερήσια σύνοψη"
ISSUE_LABEL = "analytics"
# True = σχόλιο κάθε μέρα, ακόμα και με μηδέν επισκέψεις.
# False = σχόλιο μόνο όταν υπάρχει κίνηση (και κάθε Δευτέρα, για να ξέρεις ότι ζει).
ALWAYS_POST = True

GQL = """
query ($account: String!, $site: String!, $start: Time!, $weekStart: Time!, $end: Time!) {
  viewer {
    accounts(filter: {accountTag: $account}) {
      totals: rumPageloadEventsAdaptiveGroups(
        filter: {siteTag: $site, datetime_geq: $start, datetime_lt: $end}, limit: 1
      ) { count sum { visits } }
      week: rumPageloadEventsAdaptiveGroups(
        filter: {siteTag: $site, datetime_geq: $weekStart, datetime_lt: $end}, limit: 1
      ) { count sum { visits } }
      paths: rumPageloadEventsAdaptiveGroups(
        filter: {siteTag: $site, datetime_geq: $start, datetime_lt: $end},
        limit: 10, orderBy: [count_DESC]
      ) { count dimensions { requestPath } }
      countries: rumPageloadEventsAdaptiveGroups(
        filter: {siteTag: $site, datetime_geq: $start, datetime_lt: $end},
        limit: 5, orderBy: [count_DESC]
      ) { count dimensions { countryName } }
    }
  }
}
"""

def post(url, payload, token, method="POST"):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "marmelanna-analytics"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")

def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "marmelanna-analytics"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def main():
    cf_token   = os.environ["CF_API_TOKEN"]
    account    = os.environ["CF_ACCOUNT_ID"]
    gh_token   = os.environ["GITHUB_TOKEN"]
    repo       = os.environ["GITHUB_REPOSITORY"]

    day   = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    start = f"{day}T00:00:00Z"
    week  = f"{day - timedelta(days=6)}T00:00:00Z"
    end   = f"{day + timedelta(days=1)}T00:00:00Z"

    res = post("https://api.cloudflare.com/client/v4/graphql",
               {"query": GQL,
                "variables": {"account": account, "site": SITE_TAG,
                              "start": start, "weekStart": week, "end": end}},
               cf_token)

    # Το GraphQL του Cloudflare επιστρέφει 200 ακόμα κι όταν αποτυγχάνει.
    # Χωρίς αυτόν τον έλεγχο το workflow θα «πετύχαινε» στέλνοντας κενά νούμερα.
    if res.get("errors"):
        print("Το Cloudflare GraphQL επέστρεψε σφάλματα:", file=sys.stderr)
        print(json.dumps(res["errors"], indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    accounts = (res.get("data") or {}).get("viewer", {}).get("accounts") or []
    if not accounts:
        print("Καμία απάντηση για αυτό το account. Λάθος CF_ACCOUNT_ID ή "
              "το token δεν έχει δικαίωμα Account Analytics → Read.", file=sys.stderr)
        print(json.dumps(res, indent=2)[:2000], file=sys.stderr)
        return 1

    a       = accounts[0]
    totals  = a["totals"][0] if a.get("totals") else {"count": 0, "sum": {"visits": 0}}
    views   = totals.get("count", 0)
    visits  = (totals.get("sum") or {}).get("visits", 0)
    wk      = a["week"][0] if a.get("week") else {"count": 0, "sum": {"visits": 0}}
    wk_views  = wk.get("count", 0)
    wk_visits = (wk.get("sum") or {}).get("visits", 0)

    if not ALWAYS_POST and views == 0 and day.weekday() != 0:
        print(f"{day}: μηδέν επισκέψεις, δεν στέλνω σχόλιο (ALWAYS_POST=False)")
        return 0

    lines = [f"### {day.strftime('%d/%m/%Y')}", "",
             f"**{visits}** επισκέψεις · **{views}** προβολές σελίδων",
             f"<sub>Επτά ημέρες: {wk_visits} επισκέψεις · {wk_views} προβολές</sub>", ""]

    paths = [p for p in a.get("paths", []) if p["count"]]
    if paths:
        lines.append("| Σελίδα | Προβολές |")
        lines.append("|---|---:|")
        for p in paths:
            path = p["dimensions"]["requestPath"]
            note = "  ← QR" if path == "/q" else ""
            lines.append(f"| `{path}`{note} | {p['count']} |")
        lines.append("")

    countries = [c for c in a.get("countries", []) if c["count"]]
    if countries:
        lines.append("Χώρες: " + " · ".join(
            f"{c['dimensions']['countryName']} {c['count']}" for c in countries))
        lines.append("")

    lines.append("<sub>Cloudflare Web Analytics. Υποεκτιμά όσους έχουν "
                 "ad-blocker ή JavaScript κλειστό — διάβασέ το ως τάση.</sub>")
    body = "\n".join(lines)

    # Βρες ή φτιάξε το μόνιμο issue
    issues = get(f"https://api.github.com/repos/{repo}/issues"
                 f"?state=open&labels={ISSUE_LABEL}&per_page=1", gh_token)
    if issues:
        number = issues[0]["number"]
    else:
        created = post(f"https://api.github.com/repos/{repo}/issues",
                       {"title": ISSUE_TITLE, "labels": [ISSUE_LABEL],
                        "body": "Αυτόματη ημερήσια σύνοψη. Κάθε μέρα προστίθεται "
                                "σχόλιο με τα χθεσινά νούμερα.\n\n"
                                "Για να σταματήσει: κλείσε το issue ή "
                                "απενεργοποίησε το workflow στα Actions."},
                       gh_token)
        number = created["number"]

    post(f"https://api.github.com/repos/{repo}/issues/{number}/comments",
         {"body": body}, gh_token)
    print(f"{day}: {visits} επισκέψεις, {views} προβολές → issue #{number}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
