#!/usr/bin/env python3
"""Reproduce the SF01 provenance-led discovery pool from verified Commons listings.
The listed titles were observed in Commons search results/category file lists on 2026-10-30.
This is only a source discovery seed; no image has been visually reviewed.
"""
import csv, json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
# Each category was inspected during the sourcing conversation. Titles were
# transcribed as shown, never derived from the prompt or invented.
SOURCES = {
"sheep-pasture": ("https://commons.wikimedia.org/wiki/Category:Grazing_sheep", """
A field of sheep near Stoke Golding - geograph.org.uk - 961849.jpg
236 Sheep graze in Horseshoe Basin, Pasayten Wilderness, Okanogan Nat'l Forest 1966 (36042439862).jpg
2023-01-29 Sheep above Ortachala.jpg
Afternoon landscape with sheep and shepherds at the Pester Plateau in Serbia.jpg
Chebororwa hills.jpg
Deichschaf47.jpg
Ecological lawn mower squad.jpg
Grazing sheep in Kumrat Valley.jpg
View from Moore Abbey.jpg
Grazing sheep from The Powerhouse Museum Collection.jpg
Dyr ved Sølyst.jpg
"""),
"birds-flocks": ("https://commons.wikimedia.org/wiki/Category:Flocks_of_birds", """
2017-03-11 Migratory storks resting in Rahat.jpg
2017-08-09 Valleyview Alberta (37348662380).jpg
2024-06-06 Tarangire birds 0723.jpg
A flock of seagulls flying over and floating on the sea (AM 75877-1).jpg
A large flock of birds flying a bit offshore (5045645869).jpg
Aflockalypse (8309665916).jpg
Agelaius phoeniceus Mecca CA 01.jpg
American Herring Gulls Larus smithsonianus Vancouver Island, many juveniles 7208.jpg
Greater flamingos (Phoenicopterus roseus) and other birds on the silt at sunrise, Parque Papa Francisco, Lisbon, Portugal julesvernex2.jpg
Grus canadensis -Merced National Wildlife Refuge, California, USA -flock-8.jpg
Grus grus flocks.jpg
Grey Heron on Lake Naivasha (5232076309).jpg
Group of Brewer's Blackbird.jpg
Groupe d'oiseaux marins sur la plage de l'île Moucha, Djibouti.jpg
"""),
"birds-beaches": ("https://commons.wikimedia.org/wiki/Category:Birds_on_beaches", """
Plage de l'île Moucha avec des groupes d'oiseaux marins le long de la mer émeraude, Djibouti.jpg
Jeffreys Bay Grey-headed gull 54304827610.jpg
"""),
"bales": ("https://commons.wikimedia.org/wiki/Category:Round_hay_bales_in_the_United_States", """
Amish Country Byway - Bales of Hay in Field - NARA - 7716994.jpg
Amish Country Byway - Marshmallow Hay Bales in Field - NARA - 7716912.jpg
Foggy grasslands (9816823626).jpg
Hay bales.JPG
Hay Rolls (Malheur County, Oregon scenic images) (malDA0130).jpg
Martin-farm-fields-ga.jpg
Summer Lake Area Hayfield (Lake County, Oregon scenic images) (lakDA0053).jpg
"""),
"bales-england": ("https://commons.wikimedia.org/wiki/Category:Round_hay_bales_in_England", """
A good day for making hay. - geograph.org.uk - 1185740.jpg
Baled field at Wellington Farm - geograph.org.uk - 4639860.jpg
Bales and Scoreby Wood - geograph.org.uk - 425313.jpg
Bales at Cowslip farm - geograph.org.uk - 284942.jpg
Bales at Lower Tedgewood Farm - geograph.org.uk - 528636.jpg
Bails (6112275561).jpg
"""),
"bales-norway": ("https://commons.wikimedia.org/wiki/Category:Round_hay_bales_in_Norway", """
Fields - Flam, Norway - panoramio.jpg
Hay bales in Trollholmsund in Porsanger, Troms og Finnmark, Norway, 2022 August.jpg
Round bales at Ullsfjorden, Lyngen, Troms, Norway, 2014 August.jpg
"""),
"marinas": ("https://commons.wikimedia.org/wiki/Category:Aerial_photographs_of_marinas", """
Aerial of Bogense Harbour.jpg
Aerial View Kühlungsborn Luftbild Marina.jpg
Aerial view of Cullen Bay Marina, Darwin.jpg
Aerial view of Port Alaçatı, Çeşme.jpg
Aurlahti 2021-07-24.jpg
Bahia Marina em visão aérea.jpg
Brighton Marina.jpg
Coyote Point Marina - San Mateo (49811517707).jpg
Downtown Coconut Grove.jpg
Hasle Havn asv2024-07 img06.jpg
Marina aerial southbasin.jpg
Marina being built near Bilbao, Spain (10759196943).jpg
Pampas Marina.JPG
Tel Aviv Marina aerial photo.jpg
"""),
"cars": ("https://commons.wikimedia.org/wiki/Category:Aerial_photographs_of_car_parks", """
231119-12 Chandler Fashion Center.jpg
AtlantaParkAndRideLot-Oct2015 (32668306551).jpg
Autos auf der Start und Landebahn.jpg
BassettPlace-US62-Int10-ElPasoAerial (37228766574).jpg
Downtown East Minneapolis, 2013 (17219525849).jpg
LKQ of South Texas Aerial (29753055318).jpg
Mall of America (2185193350).jpg
Parking lot, Gross-Gerau (P1090665).jpg
Scioto Downs.jpg
So May Hyundais (52701143848).jpg
Sun Ray Shopping Center.jpg
Surface Parking Lot, Downtown Minneapolis (433836865).jpg
SUVs on the Runways (40082683565).jpg
Tel Aviv parking lot.jpg
Wolapark dron.jpg
"""),
"pebbles-and-sand": ("https://commons.wikimedia.org/wiki/Category:Close-up_photographs_of_sand", """
Beach-sand-stones-pebbles (23959011919).jpg
Arena Gruesa.jpg
Cay sand.JPG
"""),
"pebbles": ("https://commons.wikimedia.org/wiki/Category:Pebbles", """
411 River pebbles.JPG
A depiction of Pebbles.jpg
"""),
"shells": ("https://commons.wikimedia.org/wiki/Category:Shells_on_beaches", """
030527-1-TheGulfofFinland-IMG 0483-2.jpg
Boulders-5198, Dingle Peninsula, Co. Kerry, Ireland.jpg
Norderney, Strand, Muscheln -- 2025 -- 8993.jpg
Sea shells by the sea Shore.jpg
Shells of Matsuura Lagoon (30715181183).jpg
Shells on Noosa North Shore beach, Queensland, 2026, 01.jpg
"""),
"boulders": ("https://commons.wikimedia.org/wiki/Category:Boulder_fields", """
Boulder fields and clouds - geograph.org.uk - 219291.jpg
Boulders above Coire Scamadal - geograph.org.uk - 217461.jpg
Cannonball Rock field, Jordan.JPG
Chalamain Gap - geograph.org.uk - 262412.jpg
Harrat al-Sham near Azraq.jpg
HighlandSprengisandur.jpg
Kamenne more Vyhne 2.JPG
Rocks on ground pattern.jpg
Shore near Jura Forest - geograph.org.uk - 134677.jpg
Stonefree (157409115).jpeg
Камни. Валуны.jpg
На плато Кукисвумчорр.jpg
"""),
"fallen-leaves": ("https://commons.wikimedia.org/wiki/Category:Dead_leaves", """
Dried Leaves & Snow.jpg
Detritus (2183217083).jpg
Dried leaves.jpg
Isolation - Flickr - Unhindered by Talent.jpg
It‘s cold outside ❄️ - Flickr - Rosmarie Voegtli.jpg
Kralupy nad Vltavou, podzimní listí.jpg
Laub.jpg
Last Leaves (260571988).jpg
"""),
"trees-scattered": ("https://commons.wikimedia.org/wiki/Category:Kingoldrum", """
Scattered trees, Ascreavie - geograph.org.uk - 7973223.jpg
"""),
"trees-grassland": ("https://commons.wikimedia.org/wiki/Category:Kirkmabreck", """
A few scattered craglets - geograph.org.uk - 3347385.jpg
"""),
}

# Individual file pages explicitly returned in source searches, unlike category leads.
DIRECT = {
"sheep-pasture": """
Field with sheep and scattered trees - geograph.org.uk - 3736076.jpg
Grazing sheep dot a verdant hillside under a brooding sky, with soft, rolling terrain evoking rural calm near Laneshaw Bridge, Colne, UK.jpg
Floral meadows with flocks of sheep.jpg
Sheep on hill.jpg
Sheep On A Hillside (Unsplash).jpg
Sheep on the hillside - geograph.org.uk - 8387712.jpg
Выпас стада овец на скошенном поле.jpg
View of many sheep along hillside (AM 79138-1).jpg
""",
"bales": """
Hay Bales in Field.jpg
Round hay bales on a field, with hawkweed in the foreground, near Durnal, Yvoir, 2025.jpg
""",
"marinas": """
Boats in the Marina.jpg
Boats on the water.jpg
DSC 6369 Tranquil shoreline with small boats bobbing on calm blue water and green hills in the background.jpg
""",
"cars": """
12 Parking garage rooftop in Chicago - many cars in a car park.jpg
Aerial view of parking lot (53581689348).jpg
""",
"pebbles-and-sand": """
Pebbles on sand.JPG
Sand and Gravel.jpg
Sand and small pebbles.jpg
Crumbled stone on sand.jpg
""",
"fallen-leaves": """
Fallen autumn leaves.jpg
Fallen aspen leaves covered with snow.jpg
Fallen fruits and leaves scattered on the ground during autumn season.jpg
Fallen autumn leaves are scattered on the surface of a puddle, reflecting a cloudy sky above.jpg
Fallen Leaves.jpg
""",
"trees-scattered": """
Savanna (242734021).jpeg
Aerial view of dry trees (Unsplash).jpg
Dead Trees on a parched landscape (30896474392).jpg
Sunrise over grassland in Uganda.jpg
Heather, rough grassland and scattered trees. - geograph.org.uk - 205695.jpg
Grassland Guardians of Warrandyte.jpg
""",
"beach-umbrellas": """
Clarity from above (Unsplash).jpg
Cocoa Beach vibes (Unsplash).jpg
Empty beach from above 1 (Unsplash).jpg
Beach umbrellas.JPG
""",
"distant-crowds": """
Festival of nets and muddy joy.jpg
Crowds of people on Santa Monica Beach, ca.1900 (CHS-820).jpg
Festival From Above.jpg
""",
}

# Keep only observed source page metadata, not guessed author/license data.
OBSERVED = {
"Grazing sheep dot a verdant hillside under a brooding sky, with soft, rolling terrain evoking rural calm near Laneshaw Bridge, Colne, UK.jpg": ("Orbitalscreams","CC BY-SA 4.0",3735,2806),
"Field with sheep and scattered trees - geograph.org.uk - 3736076.jpg": ("Trevor Littlewood","CC BY-SA 2.0",1500,782),
"Sheep on hill.jpg": ("Olena Hudyma",None,5184,3456),
"Sheep On A Hillside (Unsplash).jpg": ("Luke Ellis-Craven",None,6000,4000),
"Sheep on the hillside - geograph.org.uk - 8387712.jpg": ("Bill Nicholls",None,1024,768),
"Floral meadows with flocks of sheep.jpg": ("Zcvetkovic",None,3800,2524),
"Выпас стада овец на скошенном поле.jpg": ("Vitaliy VK",None,4896,3672),
"View of many sheep along hillside (AM 79138-1).jpg": ("Tudor Washington Collins",None,1275,949),
"Hay Bales in Field.jpg": ("Sjgdzn",None,3264,2448),
"Boats in the Marina.jpg": ("Alabama Extension","CC0 1.0",2256,1504),
"Boats on the water.jpg": ("Musunny.95",None,4000,2436),
"12 Parking garage rooftop in Chicago - many cars in a car park.jpg": ("Marek Ślusarczyk",None,2400,1600),
"Pebbles on sand.JPG": ("Barelyhere","CC0 1.0",4000,3000),
"Sand and Gravel.jpg": ("Paul The Writer","CC0 1.0",3072,4080),
"Sand and small pebbles.jpg": (None,"Public domain (Commons page)",1024,768),
"Fallen fruits and leaves scattered on the ground during autumn season.jpg": ("Shixart1985",None,6016,4016),
"Fallen aspen leaves covered with snow.jpg": (None,None,3888,2592),
"Fallen autumn leaves.jpg": ("Benjamin D. Esham",None,2815,1877),
"Savanna (242734021).jpeg": ("Mingyang Liu",None,2000,1500),
"Aerial view of dry trees (Unsplash).jpg": ("Benjamin Sloth Lindgreen",None,4000,2250),
"Sunrise over grassland in Uganda.jpg": ("Oliversamson1",None,4080,2296),
"Grassland Guardians of Warrandyte.jpg": (None,None,3840,2160),
"Clarity from above (Unsplash).jpg": ("Mikael Cho",None,3534,2160),
"Cocoa Beach vibes (Unsplash).jpg": ("Annie Spratt",None,2000,3280),
"Empty beach from above 1 (Unsplash).jpg": ("Benjamin Voros",None,3992,2242),
"Festival From Above.jpg": ("Amdadphoto",None,4000,3000),
}

rows=[]
seen={}
for family, (url, block) in SOURCES.items():
    for title in (line.strip() for line in block.strip().splitlines()):
        if not title or title in seen: continue
        seen[title]=True
        rows.append(dict(family=family, commons_filename=title, discovery="category_listing", discovery_url=url))
for family, block in DIRECT.items():
    for title in (line.strip() for line in block.strip().splitlines()):
        if not title:continue
        if title in seen:continue
        seen[title]=True
        rows.append(dict(family=family,commons_filename=title,discovery="file_page",discovery_url=None))
rows.sort(key=lambda r:(r['family'],r['commons_filename'].casefold()))
for i,r in enumerate(rows,1):
    title=r['commons_filename']
    page='https://commons.wikimedia.org/wiki/'+quote('File:'+title.replace(' ','_'),safe='():,.-_!\'')
    r.update({
        'candidate_id':f'sf-{i:04d}',
        'priority':'normal',
        'accent_color':None,
        'candidate_basis':'Listed in Commons category; potential speckling not visually checked.' if r['discovery']=='category_listing' else 'Commons file page found with search text consistent with possible speckling; thumbnail not inspected.',
        'commons_title':'File:'+title,
        'file_page':page,
        'discovery_url':r['discovery_url'] or page,
        'screening_status':'pending_visual_review',
        'visual_reason':None,
        'review_notes':'Thumbnail not acquired; do not count as visually accepted.',
        'image_downloaded':False,
        'visually_accepted':None,
        'source_independence_confirmed':None,
        'source_independence_notes':None,
        'contains_people':None,
        'creator':None,'license':None,'license_url':None,
        'original_width':None,'original_height':None,
        'acquired_url':None,'acquired_width':None,'acquired_height':None,'acquired_sha256':None,
        'acquired_path':None,'acquired_format':None,
        'preview_url':None,'preview_width':None,'preview_height':None,'preview_sha256':None,'preview_path':None,
        'metadata_path':None,'source_license_checked':False,
    })
    if title in OBSERVED:
        creator,lic,w,h=OBSERVED[title]
        r.update(creator=creator, license=lic, original_width=w, original_height=h)
        r['review_notes']='Source page metadata partly observed; thumbnail still not viewed.'

# Reorder with original RG01 keys first and new keys afterward.
old_keys=['family','commons_filename','discovery','discovery_url','candidate_basis','priority','accent_color','candidate_id','commons_title','file_page','screening_status','image_downloaded','visually_accepted','source_independence_confirmed','contains_people','creator','license','license_url','original_width','original_height','acquired_url','acquired_width','acquired_height','acquired_sha256']
new_keys=list(dict.fromkeys(old_keys + [k for row in rows for k in row.keys()]))
path=ROOT/'provenance/intake/candidates.jsonl'
with path.open('w',encoding='utf-8') as f:
    for r in rows:f.write(json.dumps({k:r.get(k) for k in new_keys},ensure_ascii=False)+'\n')
with (ROOT/'provenance/intake/candidates.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=new_keys);w.writeheader();w.writerows(rows)
print('Wrote',len(rows),'candidates in',len({r['family'] for r in rows}),'discovery buckets')
from collections import Counter
print(Counter(r['family'] for r in rows))
