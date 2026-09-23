#!/usr/bin/env python3
"""
Ημερήσια σύνοψη επισκεψιμότητας από το Cloudflare Web Analytics.

Τρέχει από GitHub Actions και γράφει σχόλιο σε ένα μόνιμο issue — το GitHub
στέλνει το email.

ΧΩΡΙΣ ΦΙΛΤΡΟ siteTag, σκόπιμα. Το dataset είναι ήδη περιορισμένο στον
λογαριασμό μέσω του accountTag, και ο λογαριασμός έχει ένα site. Δύο
προηγούμενες εκδοχές φιλτράριζαν κατά siteTag υποθέτοντας ότι είναι το token
του beacon — δεν είναι, οπότε το φίλτρο δεν ταίριαζε ποτέ και το GraphQL
επέστρεφε κενό χωρίς σφάλμα, ενώ το dashboard έδειχνε κίνηση.

Αν κάποτε προστεθεί δεύτερο site στον ίδιο λογαριασμό, τα νούμερα θα
αθροίζονται. Η ανάλυση ανά site στο τέλος του σχολίου το κάνει ορατό, και
τότε μπαίνει φίλτρο με το πραγματικό tag.

Μεταβλητές: CF_API_TOKEN, CF_ACCOUNT_ID (secrets)
            GITHUB_TOKEN, GITHUB_REPOSITORY (αυτόματα από το Actions)
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

ISSUE_TITLE = "Επισκεψιμότητα — ημερήσια σύνοψη"
ISSUE_LABEL = "analytics"
ALWAYS_POST = True          # False = σχόλιο μόνο όταν υπάρχει κίνηση
CF_GQL      = "https://api.cloudflare.com/client/v4/graphql"

MAIN_Q = """
query ($account: String!, $start: Time!, $end: Time!, $recentStart: Time!, $now: Time!) {
  viewer { accounts(filter: {accountTag: $account}) {
    totals: rumPageloadEventsAdaptiveGroups(
      filter: {datetime_geq: $start, datetime_lt: $end}, limit: 1
    ) { count sum { visits } }
    recent: rumPageloadEventsAdaptiveGroups(
      filter: {datetime_geq: $recentStart, datetime_lt: $now}, limit: 1
    ) { count sum { visits } }
    paths: rumPageloadEventsAdaptiveGroups(
      filter: {datetime_geq: $start, datetime_lt: $end}, limit: 10, orderBy: [count_DESC]
    ) { count dimensions { requestPath } }
    countries: rumPageloadEventsAdaptiveGroups(
      filter: {datetime_geq: $start, datetime_lt: $end}, limit: 5, orderBy: [count_DESC]
    ) { count dimensions { countryName } }
  } }
}"""

# Χωριστό αίτημα: αν το siteTag δεν είναι έγκυρη διάσταση, να μη ρίξει τη σύνοψη.
SITES_Q = """
query ($account: String!, $recentStart: Time!, $now: Time!) {
  viewer { accounts(filter: {accountTag: $account}) {
    sites: rumPageloadEventsAdaptiveGroups(
      filter: {datetime_geq: $recentStart, datetime_lt: $now}, limit: 10, orderBy: [count_DESC]
    ) { count dimensions { siteTag } }
  } }
}"""

def http(url, token, payload=None, github=False, method=None):
    h = {"Authorization": f"Bearer {token}", "User-Agent": "marmelanna-analytics"}
    if github: h["Accept"] = "application/vnd.github+json"
    data = json.dumps(payload).encode() if payload is not None else None
    if data: h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")

def gql(query, variables, token):
    res = http(CF_GQL, token, {"query": query, "variables": variables})
    if res.get("errors"):
        raise RuntimeError(json.dumps(res["errors"], ensure_ascii=False, indent=2))
    accounts = (res.get("data") or {}).get("viewer", {}).get("accounts") or []
    if not accounts:
        raise RuntimeError("Κανένα account. Λάθος CF_ACCOUNT_ID ή το token δεν "
                           "έχει Account → Account Analytics → Read.")
    return accounts[0]

def num(rows):
    if not rows: return 0, 0
    r = rows[0]
    return (r.get("sum") or {}).get("visits", 0), r.get("count", 0)

def main():
    cf, account = os.environ["CF_API_TOKEN"], os.environ["CF_ACCOUNT_ID"]
    gh, repo    = os.environ["GITHUB_TOKEN"], os.environ["GITHUB_REPOSITORY"]
    # Το issue το ανοίγει το bot, όχι ο χρήστης, οπότε το GitHub δεν τον κάνει
    # αυτόματα συνδρομητή και δεν στέλνει μέιλ. Η αναφορά με @ ειδοποιεί πάντα,
    # ανεξάρτητα από ρυθμίσεις watch ή subscribe.
    owner = repo.split("/")[0]

    day    = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    now    = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    vars_  = {"account": account,
              "start": f"{day}T00:00:00Z",
              "end":   f"{day + timedelta(days=1)}T00:00:00Z",
              "recentStart": f"{day - timedelta(days=29)}T00:00:00Z",
              "now": now}
    try:
        a = gql(MAIN_Q, vars_, cf)
    except RuntimeError as e:
        print("Το Cloudflare GraphQL απέτυχε:\n" + str(e), file=sys.stderr)
        return 1

    visits, views       = num(a.get("totals"))
    r_visits, r_views   = num(a.get("recent"))

    if not ALWAYS_POST and views == 0 and day.weekday() != 0:
        print(f"{day}: μηδέν επισκέψεις, δεν στέλνω σχόλιο")
        return 0

    L = [f"### {day.strftime('%d/%m/%Y')}", "",
         f"**{visits}** επισκέψεις · **{views}** προβολές σελίδων",
         f"<sub>Τελευταίες 30 ημέρες: {r_visits} επισκέψεις · {r_views} προβολές</sub>", ""]

    paths = [p for p in a.get("paths", []) if p["count"]]
    if paths:
        L += ["| Σελίδα | Προβολές |", "|---|---:|"]
        for p in paths:
            path = p["dimensions"]["requestPath"]
            L.append(f"| `{path}`{'  ← QR' if path == '/q' else ''} | {p['count']} |")
        L.append("")

    countries = [c for c in a.get("countries", []) if c["count"]]
    if countries:
        L += ["Χώρες: " + " · ".join(
            f"{c['dimensions']['countryName']} {c['count']}" for c in countries), ""]

    # Best effort: αν ο λογαριασμός αποκτήσει δεύτερο site, να φανεί.
    try:
        sites = [s for s in gql(SITES_Q, {k: vars_[k] for k in
                 ("account", "recentStart", "now")}, cf).get("sites", []) if s["count"]]
        if len(sites) > 1:
            L += ["> ⚠ Ο λογαριασμός έχει πάνω από ένα site Web Analytics και τα "
                  "νούμερα αθροίζονται: " + " · ".join(
                  f"`{s['dimensions']['siteTag']}` {s['count']}" for s in sites), ""]
    except Exception as e:
        print(f"(ανάλυση ανά site δεν έγινε: {e})")

    L.append("<sub>Cloudflare Web Analytics. Υποεκτιμά όσους έχουν ad-blocker ή "
             "JavaScript κλειστό — διάβασέ το ως τάση.</sub>")
    L.append(f"<sub>@{owner}</sub>")

    issues = http(f"https://api.github.com/repos/{repo}/issues"
                  f"?state=open&labels={ISSUE_LABEL}&per_page=1", gh, github=True)
    if issues:
        n = issues[0]["number"]
    else:
        n = http(f"https://api.github.com/repos/{repo}/issues", gh,
                 {"title": ISSUE_TITLE, "labels": [ISSUE_LABEL],
                  "body": "Αυτόματη ημερήσια σύνοψη. Για να σταματήσει, κλείσε "
                          "το issue ή απενεργοποίησε το workflow στα Actions."},
                 github=True)["number"]
    http(f"https://api.github.com/repos/{repo}/issues/{n}/comments", gh,
         {"body": "\n".join(L)}, github=True)
    print(f"{day}: {visits} επισκέψεις, {views} προβολές (30 ημέρες: {r_visits}) → issue #{n}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
