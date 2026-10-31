#!/usr/bin/env python3
"""One-time annotations for conspicuous possible source relationships; no similarity labels."""
from acquire import ROOT, jsonlines, save_records
records=jsonlines(ROOT/'candidates.jsonl')
notes={
  "Amish Country Byway - Bales of Hay in Field - NARA - 7716994.jpg":"Possibly from the same NARA Amish Country Byway photographic series as sf candidate with 'Marshmallow Hay Bales'; do not accept both without capture independence check.",
  "Amish Country Byway - Marshmallow Hay Bales in Field - NARA - 7716912.jpg":"Possibly from the same NARA Amish Country Byway photographic series as sf candidate with 'Bales of Hay in Field'; do not accept both without capture independence check.",
  "Groupe d'oiseaux marins sur la plage de l'île Moucha, Djibouti.jpg":"Possible overlapping location/sequence with the 'Plage de l'île Moucha...' lead. Check origin and scene before accepting either/both.",
  "Plage de l'île Moucha avec des groupes d'oiseaux marins le long de la mer émeraude, Djibouti.jpg":"Possible overlapping location/sequence with the 'Groupe d'oiseaux marins...' lead. Check origin and scene before accepting either/both.",
  "Downtown East Minneapolis, 2013 (17219525849).jpg":"Potential location overlap with other Minneapolis parking candidates. Shared city alone does not prove shared capture.",
  "Surface Parking Lot, Downtown Minneapolis (433836865).jpg":"Potential location overlap with other Minneapolis parking candidates. Shared city alone does not prove shared capture.",
}
for r in records:
 if r['commons_filename'] in notes:r['source_independence_notes']=notes[r['commons_filename']]
save_records(records)
print('Flagged',sum(bool(r['source_independence_notes']) for r in records),'records with known uncertainty')
