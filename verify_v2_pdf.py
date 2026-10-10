import pymupdf

doc = pymupdf.open('EV_Charging_Analytics_Case_Study_Final_Draft_v2.pdf')
print('=== FINAL PDF v2 COMPREHENSIVE VERIFICATION ===')
print('Total pages:', len(doc))

# Check for placeholders
forbidden = ['[TO VERIFY]', 'TODO', 'TBD', 'vehicles s exhibit', 'vehicles s']
for term in forbidden:
    found = []
    for pno in range(len(doc)):
        if term.lower() in doc[pno].get_text().lower():
            found.append(pno + 1)
    if found:
        print(f'ERROR: "{term}" found on page(s): {found}')
    else:
        print(f'CLEAN: Zero occurrences of "{term}"')

# Verify key phrases
checks = [
    ('5,000 verified', 'Session count'),
    ('14,422 continuous', 'Hourly interval count'),
    ('53,668.78 kWh', 'Conserved delivered energy'),
    ('13.168 kWh', 'Validation RMSE Ridge'),
    ('15.713 kWh', 'Test RMSE Ridge'),
    ('15.633 kWh', 'Test RMSE XGBoost'),
    ('0.1158', 'Test R2 Ridge'),
    ('0.1248', 'Test R2 XGBoost'),
    ('150 sessions', 'Anomaly detector flags'),
    ('33 consensus', 'Intersection count'),
    ('267 distinct', 'Union count'),
    ('117 sessions', 'Unique flags per detector'),
    ('234 sessions', 'Symmetric difference count'),
    ('4.87x', 'Energy ratio'),
    ('7.23x', 'Idle dwell ratio'),
    ('1.30 hours', 'Median dwell buffer'),
    ('January 21, 2020', 'Chronological start date'),
    ('April 30, 2021', 'Training partition end date'),
    ('May 1', 'Validation start date'),
    ('June 30, 2021', 'Validation end date'),
    ('July 1', 'Test start date'),
    ('September 13, 2021', 'Test end date')
]

for phrase, desc in checks:
    found = False
    for page in doc:
        if phrase.lower() in page.get_text().lower():
            found = True
            break
    status = 'VERIFIED' if found else 'MISSING'
    print(f'[{status}] {desc}: "{phrase}"')
