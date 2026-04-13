import re

PLAYER_PRICES = {
    "Virat Kohli": 305, "Travis Head": 160, "Aiden Markram": 140, "Arshdeep Singh": 100,
    "KL Rahul": 85, "Varun Chakaravarthy": 65, "Rajat Patidar": 40, "Rinku Singh": 20,
    "Ruturaj Gaikwad": 25, "Vipraj Nigam": 10, "Shashank Singh": 10, "Noor Ahmad": 10,
    "Harsh Dubey": 10, "Tushar Deshpande": 10, "Vijaykumar Vyshak": 10,
    "Shreyas Iyer": 270, "Ravindra Jadeja": 155, "Nicholas Pooran": 190, "Jos Buttler": 160,
    "Shimron Hetmyer": 55, "Harshal Patel": 20, "Ajinkya Rahane": 40, "Vaibhav Arora": 15,
    "Liam Livingstone": 15, "Rahul Tewatia": 15, "Jitesh Sharma": 15, "Marcus Stoinis": 15,
    "Romario Shepherd": 15, "Cameron Green": 10, "Kagiso Rabada": 10,
    "Abhishek Sharma": 200, "Yashasvi Jaiswal": 190, "Mitchell Marsh": 110, "Rishabh Pant": 90,
    "Yuzvendra Chahal": 70, "Marco Jansen": 70, "Nitish Kumar Reddy": 35, "Ryan Rickelton": 40,
    "Vaibhav Sooryavanshi": 50, "Tim David": 40, "Tristan Stubbs": 20, "Shardul Thakur": 20,
    "Riyan Parag": 20, "Mitchell Santner": 35, "Eshan Malinga": 10,
    "Suryakumar Yadav": 170, "Sunil Narine": 150, "Rohit Sharma": 200, "Tilak Varma": 120,
    "Jofra Archer": 60, "Priyansh Arya": 60, "Nehal Wadhera": 30, "Mohammed Siraj": 20,
    "Deepak Chahar": 20, "Prabhsimran Singh": 40, "Ayush Mhatre": 45, "Bhuvneshwar Kumar": 30,
    "Aniket Verma": 15, "David Miller": 20, "Sherfane Rutherford": 10,
    "Jasprit Bumrah": 170, "Heinrich Klaasen": 205, "Shivam Dube": 170, "Sai Sudharsan": 190,
    "Axar Patel": 90, "Naman Dhir": 25, "Angkrish Raghuvanshi": 50, "Krunal Pandya": 30,
    "Ayush Badoni": 10, "Mohammad Shami": 10, "Washington Sundar": 10, "Jamie Overton": 10,
    "Lungi Ngidi": 10, "Glenn Phillips": 10, "Jacob Duffy": 10,
    "Ishan Kishan": 230, "Hardik Pandya": 190, "Shubman Gill": 110, "Phil Salt": 85,
    "Rashid Khan": 55, "Kuldeep Yadav": 30, "Sanju Samson": 70, "Khaleel Ahmed": 20,
    "Devdutt Padikkal": 35, "Dhruv Jurel": 40, "Prasidh Krishna": 25, "Sameer Rizvi": 25,
    "Anshul Kamboj": 10, "Ravi Bishnoi": 15, "Cooper Connolly": 20,
}

with open("/Users/mom/Desktop/IplFantasy/docs/index.html") as f:
    html = f.read()

# --- CSS additions ---
html = html.replace(
    "  .today-pts { font-size: 1em; font-weight: 600; color: #f9cd05; text-align: right; }",
    "  .today-pts { font-size: 1em; font-weight: 600; color: #f9cd05; text-align: right; }\n"
    "  .price { color: #4cff9f; font-size: 0.85em; }\n"
    "  .pct { color: #aaa; font-size: 0.85em; }\n"
    "  .col-toggle { display: inline-block; margin: 0 0 12px; padding: 5px 14px; background: #1a1f3d; color: #aaa; border: 1px solid #2a2f55; border-radius: 6px; font-size: 0.8em; cursor: pointer; user-select: none; }\n"
    "  .col-toggle.active { color: #4cff9f; border-color: #4cff9f; }\n"
    "  .hide-bc .col-bc { display: none; }"
)

# --- Hide by default ---
html = html.replace('<div class="container">', '<div class="container hide-bc">')

# --- Toggle button before first card ---
first_card = html.index('\n    <div class="card">')
html = html[:first_card] + '\n  <span class="col-toggle" onclick="toggleBC(this)">Show Before / Current</span>' + html[first_card:]

# --- Player table headers: reorder + add Price, % ---
# Git HTML already reordered: Player, Before, Current, Today, Points
# New: Player, Price, Before(col-bc), Current(col-bc), Today, Points, %
old_header = '<thead><tr><th onclick="sortTable(this)">Player</th><th onclick="sortTable(this)">Before</th><th onclick="sortTable(this)">Current</th><th onclick="sortTable(this)">Today</th><th onclick="sortTable(this)">Points</th></tr></thead>'
new_header = '<thead><tr><th onclick="sortTable(this)">Player</th><th onclick="sortTable(this)">Price</th><th onclick="sortTable(this)" class="col-bc">Before</th><th onclick="sortTable(this)" class="col-bc">Current</th><th onclick="sortTable(this)">Today</th><th onclick="sortTable(this)">Points</th><th onclick="sortTable(this)">%</th></tr></thead>'
html = html.replace(old_header, new_header)

# --- Extract team totals for % calc ---
team_totals = [int(x) for x in re.findall(r'card-pts">(\d+) pts', html)]
print(f"Team totals: {team_totals}")

# --- Process each card's rows ---
cards = html.split('<div class="card">')
new_cards = [cards[0]]

for i, card in enumerate(cards[1:]):
    total = team_totals[i] if i < len(team_totals) else 1

    def process_row(m, total=total):
        row = m.group(0)

        # Extract player name
        name_match = re.search(r'<td>([^<]+?)\s*<span class="ipl-team">', row)
        name = name_match.group(1).strip() if name_match else ""
        price = PLAYER_PRICES.get(name, 0)

        # Original td order: player, today, before, current, points
        # Extract values
        num_tds = re.findall(r'<td class="num[^"]*">([^<]+)</td>', row)
        # num_tds[0]=today, num_tds[1]=before, num_tds[2]=current, num_tds[3]=points
        if len(num_tds) < 4:
            return row

        # Git HTML order: before, current, today, points
        before_val = num_tds[0]
        current_val = num_tds[1]
        today_val = num_tds[2]
        points_val = num_tds[3]

        # Determine points class
        pts_num = int(points_val.replace('+', ''))
        pts_class = "pos" if pts_num > 0 else "neg" if pts_num < 0 else ""

        # Calculate %
        pct = round(pts_num / total * 100, 1) if total else 0
        pct_str = f"{pct:.1f}" if pct != int(pct) else f"{int(pct)}"

        # Get tr class
        tr_class = re.search(r'<tr class="([^"]*)">', row).group(1)

        # Rebuild row: Player, Price, Before(col-bc), Current(col-bc), Today, Points, %
        player_td = name_match.group(0).replace(name_match.group(0), f'<td>{name} <span class="ipl-team">')
        # Get full player td
        player_full = re.search(r'<td>[^<]+<span class="ipl-team">[^<]*</span></td>', row).group(0)

        new_row = f"""            <tr class="{tr_class}">
              {player_full}
              <td class="num price">{price}L</td>
              <td class="num col-bc">{before_val}</td>
              <td class="num col-bc">{current_val}</td>
              <td class="num today-pts">{today_val}</td>
              <td class="num {pts_class}">{points_val}</td>
              <td class="num pct">{pct_str}%</td>
            </tr>"""
        return new_row

    card = re.sub(r'<tr class="[^"]*">\s*<td>[^<]+<span class="ipl-team">.*?</tr>', process_row, card, flags=re.DOTALL)
    new_cards.append(card)

html = '<div class="card">'.join(new_cards)

# --- Add toggleBC JS ---
html = html.replace(
    "function sortTable(th) {",
    "function toggleBC(btn) {\n"
    "  document.querySelector('.container').classList.toggle('hide-bc');\n"
    "  btn.classList.toggle('active');\n"
    "}\n"
    "function sortTable(th) {"
)

with open("/Users/mom/Desktop/IplFantasy/docs/index.html", "w") as f:
    f.write(html)

# Verify
with open("/Users/mom/Desktop/IplFantasy/docs/index.html") as f:
    result = f.read()
print(f"pct cells: {result.count('num pct')}")
print(f"price cells: {result.count('num price')}")
print(f"col-bc cells: {result.count('col-bc')}")

# Show a sample row
sample = re.search(r'<tr class="">\s*<td>Shubman Gill.*?</tr>', result, re.DOTALL)
if sample:
    print("\nSample row (Shubman Gill):")
    print(sample.group(0))
