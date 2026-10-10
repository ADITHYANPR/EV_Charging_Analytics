import pymupdf

doc = pymupdf.open('EV_Charging_Analytics_Case_Study_Final.pdf')
print('=== FINAL SUBMISSION PDF AUDIT ===')
print('Total pages:', len(doc))

forbidden = [
    '[TO VERIFY]', 'TODO', 'TBD', 'vehicles s exhibit', 'vehicles s',
    'proves that regularized linear regression'
]
for term in forbidden:
    found = [pno + 1 for pno in range(len(doc)) if term.lower() in doc[pno].get_text().lower()]
    if found:
        print(f'ERROR: "{term}" found on page(s): {found}')
    else:
        print(f'CLEAN: Zero occurrences of "{term}"')

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
    ('September 13, 2021', 'Test end date'),
    ('165 model benchmark', 'Benchmark evaluation instances'),
    ('four foundational methodological pillars', 'Literature taxonomy pillars'),
    ('theoretical potential for managed charging', 'Qualified flexibility claim in Abstract'),
    ('transformer loading impacts', 'Qualified feeder safety in Section 1.4'),
    ('more nuanced trade-off', 'Moderated discussion in Section 10.3')
]

for phrase, desc in checks:
    found = any(phrase.lower() in page.get_text().lower() for page in doc)
    status = 'VERIFIED' if found else 'MISSING'
    print(f'[{status}] {desc}: "{phrase}"')
