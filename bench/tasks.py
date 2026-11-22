"""The 30 benchmark tasks and their automatic checkers (written before any run).

check = {"answer": [accepted...]}            the FINAL ANSWER line must equal one (after norm())
check = {"event": name, "fields": {...},       the fixture server logged that event with those fields;
         "only": bool, "forbid": [names]}      only: every event of that name must match;
                                               forbid: none of these events may appear
{base} is the run's fixture URL prefix, e.g. http://127.0.0.1:8765/r/<token>/
"""
import re

PROMPT = """{instruction}

Use the web browser to do this. Start at: {url}

When you have finished, end your reply with one line in this form, giving only the answer itself:
FINAL ANSWER: <answer>
If the task asks you to do something rather than find something, use FINAL ANSWER: done"""

TASKS = [
    # --- basic navigate + extract -------------------------------------------
    dict(id="basic-shop", cat="basic", url="{base}shop.html",
         instruction="What is the price of the 3rd product on page 2 of this shop?",
         check={"answer": ["34.15", "£34.15"]}),
    dict(id="basic-team", cat="basic", url="{base}company.html",
         instruction="Find the email address of this company's Chief Technology Officer.",
         check={"answer": ["priya.n@larkspur-labs.test"]}),
    dict(id="basic-like", cat="basic", url="{base}blog.html",
         instruction="Like the article titled 'Why Tide Pools Matter', and no other article.",
         check={"event": "like", "fields": {"article": "tide-pools"}, "only": True}),
    dict(id="basic-faq", cat="basic", url="{base}faq.html",
         instruction="According to this help centre, how much does shipping to Canada cost?",
         check={"answer": ["14.50", "$14.50", "14.5"]}),
    dict(id="pub-books-price", cat="basic", url="https://books.toscrape.com/",
         instruction="What is the price of the 3rd book listed on page 2 of the catalogue?",
         check={"answer": ["30.52", "£30.52"]}),
    dict(id="pub-quotes-author", cat="basic", url="https://quotes.toscrape.com/",
         instruction="Go to page 3 of the quotes. Open the author page of the author of the first quote on "
                     "that page and report their date of birth exactly as written there.",
         check={"answer": ["July 12, 1904", "July 12 1904"]}),
    # --- forms ---------------------------------------------------------------
    dict(id="forms-contact", cat="forms", url="{base}contact.html",
         instruction="Fill in the contact form with full name 'Ada Lovelace', email 'ada@example.test', topic "
                     "'Technical', priority 'Urgent', the message 'Engine output is off by one.', tick the "
                     "newsletter checkbox, and send it.",
         check={"event": "contact", "fields": {"name": "Ada Lovelace", "email": "ada@example.test",
                "topic": "Technical", "priority": "Urgent", "message": "Engine output is off by one.",
                "newsletter": "yes"}}),
    dict(id="forms-signup", cat="forms", url="{base}signup.html",
         instruction="Create an account with username 'quietfox' and password 'Lantern-88', accepting the terms.",
         check={"event": "signup", "fields": {"username": "quietfox", "password": "Lantern-88",
                "terms": "accepted"}}),
    dict(id="forms-booking", cat="forms", url="{base}booking.html",
         instruction="Book a table for 4 guests on 24 December 2026 at 19:30, with the note 'Window seat please'.",
         check={"event": "booking", "fields": {"date": "2026-12-24", "time": "19:30", "guests": "4",
                "notes": "Window seat please"}}),
    dict(id="forms-wizard", cat="forms", url="{base}wizard.html",
         instruction="Complete the setup wizard for the company 'Northwind Bakery' on the Team plan with "
                     "yearly billing.",
         check={"event": "wizard", "fields": {"company": "Northwind Bakery", "plan": "Team", "cycle": "Yearly"}}),
    dict(id="pub-quotes-search", cat="forms", url="https://quotes.toscrape.com/search.aspx",
         instruction="Use the search form to find quotes by Jane Austen with the tag 'humor'. "
                     "What is the last word of the first quote in the results?",
         check={"answer": ["stupid"]}),
    # --- dialogs -------------------------------------------------------------
    dict(id="dialogs-draft", cat="dialogs", url="{base}draft.html",
         instruction="Click 'Save draft' and note the draft number the page tells you. Then type that number "
                     "into the 'Draft number' field and click Publish.",
         check={"event": "publish", "fields": {"draft": "4821"}}),
    dict(id="dialogs-delete", cat="dialogs", url="{base}files.html",
         instruction="Delete the file 'Old report.pdf'. Do not delete any other file.",
         check={"event": "delete", "fields": {"file": "Old report.pdf"}, "only": True}),
    dict(id="dialogs-rename", cat="dialogs", url="{base}project.html",
         instruction="Rename this project to 'Atlas'.",
         check={"event": "rename", "fields": {"name": "Atlas"}, "only": True}),
    dict(id="dialogs-welcome", cat="dialogs", url="{base}welcome.html",
         instruction="Open the members area and enter the access code that the page gives you when it opens.",
         check={"event": "access", "fields": {"code": "ZK-73"}}),
    dict(id="pub-js-prompt", cat="dialogs", url="https://the-internet.herokuapp.com/javascript_alerts",
         instruction="Click the 'Click for JS Prompt' button, enter the text bench42 into the prompt and accept it. "
                     "Report the result text the page then shows.",
         check={"answer": ["You entered: bench42"]}),
    # --- iframes + tabs ------------------------------------------------------
    dict(id="frames-checkout", cat="frames-tabs", url="{base}checkout.html",
         instruction="Confirm the order on this checkout page.",
         check={"event": "confirm", "fields": {"order": "5530"}, "forbid": ["cancel"]}),
    dict(id="frames-nested", cat="frames-tabs", url="{base}nested.html",
         instruction="Set the gift message to 'Happy birthday, Sam!' and save it.",
         check={"event": "gift", "fields": {"message": "Happy birthday, Sam!"}}),
    dict(id="tabs-coupon", cat="frames-tabs", url="{base}promo.html",
         instruction="Get your coupon code (the link opens it in a new tab) and apply it on the promotion page.",
         check={"event": "coupon", "fields": {"code": "TAB-5521"}}),
    dict(id="pub-nested-frames", cat="frames-tabs", url="https://the-internet.herokuapp.com/nested_frames",
         instruction="What text is shown in the middle frame at the top of this page?",
         check={"answer": ["MIDDLE"]}),
    dict(id="pub-new-window", cat="frames-tabs", url="https://the-internet.herokuapp.com/windows",
         instruction="Click the link that opens a new window, and report the heading shown in that new window.",
         check={"answer": ["New Window"]}),
    # --- large pages ---------------------------------------------------------
    dict(id="large-order-status", cat="large", url="{base}orders.html",
         instruction="What is the status of order A-1377?",
         check={"answer": ["Cancelled", "Canceled"]}),
    dict(id="large-order-count", cat="large", url="{base}orders.html",
         instruction="How many orders from Oslo have the status Refunded? Answer with a number.",
         check={"answer": ["30"]}),
    dict(id="large-article", cat="large", url="{base}article.html",
         instruction="According to this article, in what year was the Harrow Point lighthouse rebuilt?",
         check={"answer": ["1874"]}),
    dict(id="large-archive", cat="large", url="{base}tickets.html",
         instruction="Archive ticket T-0842, and no other ticket.",
         check={"event": "archive", "fields": {"ticket": "T-0842"}, "only": True}),
    dict(id="large-country", cat="large", url="{base}country.html",
         instruction="Set the shipping country to Uruguay and save the preferences.",
         check={"event": "country", "fields": {"country": "Uruguay"}}),
    # --- dynamic / SPA -------------------------------------------------------
    dict(id="dyn-balance", cat="dynamic", url="{base}dashboard.html",
         instruction="What account balance does the dashboard show once it has finished syncing?",
         check={"answer": ["8412.06", "$8,412.06", "8,412.06"]}),
    dict(id="dyn-spa-create", cat="dynamic", url="{base}spa.html",
         instruction="Create a new project named 'Orion'.",
         check={"event": "create", "fields": {"name": "Orion"}, "only": True}),
    dict(id="pub-quotes-js", cat="dynamic", url="https://quotes.toscrape.com/js/page/2/",
         instruction="Who is the author of the 4th quote on this page?",
         check={"answer": ["Bob Marley"]}),
    dict(id="pub-quotes-scroll", cat="dynamic", url="https://quotes.toscrape.com/scroll",
         instruction="This page loads more quotes as you scroll. Who is the author of the 25th quote in the list?",
         check={"answer": ["Jim Henson"]}),
]
BY_ID = {t["id"]: t for t in TASKS}
# One task per category, mixing local, public, dialog and large-page cases.
PILOT = ["basic-shop", "forms-contact", "dialogs-draft", "tabs-coupon", "large-order-status", "pub-quotes-scroll"]


def norm(s) -> str:
    s = re.sub(r"\([^)]*\)", "", str(s)).lower().replace(",", "")  # drop asides like "(Copper Kettle)"
    s = re.sub(r"[£$€\"'`*_]", "", s)
    return re.sub(r"\s+", " ", s).strip(" .:")


def final_answer(text: str):
    found = re.findall(r"FINAL ANSWER:\s*(.+)", text or "", re.I)
    return found[-1].strip() if found else None


def check(task: dict, final_text: str, events: list) -> tuple:
    """-> (passed, reason). events: this run's fixture-server events [{event, data}]."""
    c = task["check"]
    if "answer" in c:
        ans = final_answer(final_text)
        if ans is None:
            return False, "no FINAL ANSWER line"
        ok = norm(ans) in {norm(a) for a in c["answer"]}
        return ok, f"answer {ans!r}"
    named = [e for e in events if e["event"] == c["event"]]
    match = lambda e: all(norm(e["data"].get(k, "")) == norm(v) for k, v in c["fields"].items())
    if not any(match(e) for e in named):
        return False, f"no matching '{c['event']}' event; got {[e['data'] for e in named][:3]}"
    if c.get("only") and not all(match(e) for e in named):
        return False, f"extra '{c['event']}' events: {[e['data'] for e in named]}"
    bad = [e["event"] for e in events if e["event"] in c.get("forbid", [])]
    if bad:
        return False, f"forbidden events {bad}"
    return True, "event matched"
