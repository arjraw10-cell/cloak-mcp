"""Writes the large-page fixtures (deterministic) and prints the answers tasks.py expects."""
import html
import random
from pathlib import Path

OUT = Path(__file__).parent / "fixtures"
rng = random.Random(7)
HEAD = '<!doctype html><html><head><meta charset="utf-8"><title>{}</title><script src="bench.js"></script></head><body>'

# --- orders.html: 2,000-row table -------------------------------------------
cities = ["Oslo", "Lisbon", "Leeds", "Porto", "Bergen", "Ghent", "Turin", "Lyon", "Graz", "Cork", "Malmo", "Tallinn"]
statuses = ["Pending", "Shipped", "Delivered", "Refunded", "Cancelled"]
first = ["Ana", "Ben", "Chloe", "Dev", "Elif", "Finn", "Gia", "Hugo", "Iris", "Jon", "Kai", "Lena", "Mo", "Nia", "Omar", "Pia"]
last = ["Berg", "Costa", "Doyle", "Eriksen", "Fischer", "Garcia", "Haas", "Ivanov", "Jensen", "Klein", "Lund", "Moreau"]
rows, oslo_refunded = [], 0
for i in range(2000):
    oid, city, status = f"A-{1000 + i}", rng.choice(cities), rng.choice(statuses)
    if oid == "A-1377":
        status = "Cancelled"
    oslo_refunded += city == "Oslo" and status == "Refunded"
    rows.append(f"<tr><td>{oid}</td><td>{rng.choice(first)} {rng.choice(last)}</td><td>{city}</td>"
                f"<td>{status}</td><td>€{rng.randint(500, 99999) / 100:.2f}</td></tr>")
(OUT / "orders.html").write_text(
    HEAD.format("Orders") + "<h1>All orders</h1><table><tr><th>Order</th><th>Customer</th><th>City</th>"
    "<th>Status</th><th>Total</th></tr>" + "".join(rows) + "</table></body></html>", encoding="utf-8")
print("orders: A-1377 = Cancelled; Oslo+Refunded =", oslo_refunded)

# --- tickets.html: 600 rows, each with its own Archive button ----------------
subjects = ["Login fails on mobile", "Invoice total wrong", "Export to CSV broken", "Slow dashboard",
            "Password reset email missing", "Wrong timezone in reports", "Cannot upload avatar", "2FA code rejected"]
trs = "".join(
    f"<tr><td>T-{n:04d}</td><td>{rng.choice(subjects)}</td><td>{rng.choice(['Open', 'Waiting', 'Escalated'])}</td>"
    f"<td><button onclick=\"post('archive',{{ticket:'T-{n:04d}'}})\">Archive</button></td></tr>"
    for n in range(401, 1001))
(OUT / "tickets.html").write_text(
    HEAD.format("Support tickets") + '<h1>Support queue</h1><p id="status"></p><table><tr><th>Ticket</th>'
    "<th>Subject</th><th>State</th><th></th></tr>" + trs + "</table></body></html>", encoding="utf-8")
print("tickets: T-0401..T-1000")

# --- article.html: a very long article with one fact deep inside ------------
words = ("the coast harbour keepers wind tide rocks lamp oil winter boats cliffs village records ledger "
         "storm fog bell signal crew supply ship granite tower stairs gallery lens beacon night season").split()
def para():
    return " ".join(" ".join(rng.choice(words) for _ in range(rng.randint(8, 16))).capitalize() + "."
                    for _ in range(rng.randint(4, 7)))
paras = [para() for _ in range(160)]
facts = {5: "The Harrow Point lighthouse was first lit in 1821.",
         40: "Further north, the Fenwick Rock lighthouse was rebuilt in 1890 after a fire.",
         71: "A winter storm damaged the Harrow Point lantern room in 1869.",
         112: "The Harrow Point lighthouse was rebuilt in 1874 with a taller granite tower.",
         150: "The Harrow Point light was automated in 1952."}
for i, fact in facts.items():
    paras[i] = paras[i] + " " + fact
(OUT / "article.html").write_text(
    HEAD.format("A history of the north coast lights") + "<h1>A history of the north coast lights</h1>"
    + "".join(f"<p>{p}</p>" for p in paras) + "</body></html>", encoding="utf-8")
print("article: Harrow Point rebuilt = 1874")

# --- country.html: long terms text + a ~200-option select -------------------
countries = """Afghanistan Albania Algeria Andorra Angola Argentina Armenia Australia Austria Azerbaijan Bahamas Bahrain
Bangladesh Barbados Belarus Belgium Belize Benin Bhutan Bolivia Botswana Brazil Brunei Bulgaria Burundi Cambodia Cameroon
Canada Chad Chile China Colombia Comoros Croatia Cuba Cyprus Czechia Denmark Djibouti Dominica Ecuador Egypt Eritrea Estonia
Eswatini Ethiopia Fiji Finland France Gabon Gambia Georgia Germany Ghana Greece Grenada Guatemala Guinea Guyana Haiti Honduras
Hungary Iceland India Indonesia Iran Iraq Ireland Israel Italy Jamaica Japan Jordan Kazakhstan Kenya Kiribati Kuwait Kyrgyzstan
Laos Latvia Lebanon Lesotho Liberia Libya Liechtenstein Lithuania Luxembourg Madagascar Malawi Malaysia Maldives Mali Malta
Mauritania Mauritius Mexico Moldova Monaco Mongolia Montenegro Morocco Mozambique Myanmar Namibia Nauru Nepal Netherlands
Nicaragua Niger Nigeria Norway Oman Pakistan Palau Panama Paraguay Peru Philippines Poland Portugal Qatar Romania Russia Rwanda
Samoa Senegal Serbia Seychelles Singapore Slovakia Slovenia Somalia Spain Sudan Suriname Sweden Switzerland Syria Taiwan
Tajikistan Tanzania Thailand Togo Tonga Tunisia Turkey Turkmenistan Tuvalu Uganda Ukraine Uruguay Uzbekistan Vanuatu Venezuela
Vietnam Yemen Zambia Zimbabwe""".split()
opts = "".join(f"<option>{html.escape(c)}</option>" for c in countries)
terms = "".join(f"<p>{para()}</p>" for _ in range(40))
(OUT / "country.html").write_text(
    HEAD.format("Shipping preferences") + "<h1>Shipping preferences</h1><h2>Terms of carriage</h2>" + terms
    + '<form method="post" action="api/country"><p><label for="country">Shipping country</label> '
    + f'<select id="country" name="country"><option value="">Select a country</option>{opts}</select></p>'
    + '<p><button type="submit">Save preferences</button></p></form></body></html>', encoding="utf-8")
print("country: Uruguay")
