# RG01 — Small warm-colored things in big green places

**Status:** Candidate source sweep, not a completed or visually curated fixture. No image files have been downloaded.

## Collection objective

- Final set: approximately **70 distinct photographs**, potentially 50–80 if screening requires it.
- Primary visual motif: a salient **red** object within a predominantly **green** outdoor environment.
- Low-human: avoid people as primary subjects; incidental people are permissible.
- Warm orange/ochre/mustard accents are fallback, **not** an excuse to dilute the first red-focused sweep.
- Similarity is only a visual impression. Do not impose pair or membership labels as ground truth.
- Exclude scenes/provenance sequences, near-duplicates, derivative crops, reposts, and non-photographs.
- Keep original framing and colors. No square crops, forced dimensions, histogram corrections, or color normalization.

## Candidate counts

- **107** source candidates, of which **7** are warm-color fallback.
- **39** first encountered through individual Commons file pages; **68** through Commons category listings.
- These counts describe **leads**, not validated members. Titles/categories alone cannot establish visual fit or independent provenance.

| Family | Candidates |
|---|---:|
| benches | 17 |
| berries | 12 |
| bicycles | 7 |
| built-other | 6 |
| chairs | 2 |
| flower | 10 |
| fruit-berries | 8 |
| fungi | 2 |
| gates | 13 |
| green-red-objects | 2 |
| insects | 4 |
| mailboxes | 4 |
| safety-equipment | 5 |
| tents | 6 |
| umbrellas | 4 |
| vehicles-machinery | 5 |

## What remains unverified

Every record has `screening_status=pending_visual_review`. File-page names and descriptions are not a substitute for examining the image. In particular: green area, red salience, human occupancy, distinctness of scenes, creator, license, and original dimensions have not all been verified. The presence of a source link does not mean the photo is suitable.

## Screening and acquisition plan

1. Resolve Commons file metadata and **small previews first**; check existence, file type, photo/illustration distinction, attribution and reuse license. Compare candidate thumbnails on a contact sheet before making final selections.
2. Screen visual balance at thumbnail scale: substantial green foliage/grass, recognizable warm/red accent, not dominated by people or urban gray. Drop weak fits without trying to replace them with synthetic precision.
3. Check provenance: different original photographers when possible, independently taken scenes, and no series/crops/alternate resolutions. A source link does **not** prove independence.
4. Downselect to ~70 without allowing a single subject family (e.g. flowers) to dominate. No semantic `core/border/outlier` labels.
5. Download server-rendered reduced versions (nominal max dimension **1600 px**) using Commons metadata API and thumbnail URLs. Avoid fetching huge originals. Some historical images are smaller and should remain so.
6. Verify actual pixel dimensions (thumbnail service may return dimensions other than requested), file hashes, attribution, and license; produce final fixture manifest, image set, and contact sheet in a ZIP.
7. If the initial media download returns an access/rate-limit error, record status, headers and `Retry-After`, stop immediately, then diagnose. No bulk retries, no authenticated credentials until the failure is understood.

## Record structure

`candidates.jsonl` contains exact Commons filenames and file-page links; `discovery` distinguishes direct file-page leads from category-only leads. `creator`, `license`, `original_width`/`original_height`, `acquired_url`, `acquired_sha256`, etc. deliberately remain null until checked. IDs `rg-NNNN` identify **candidate rows**, not immutable fixture IDs.

## Source index

The links below are Commons file pages, **not** image download URLs. Entries marked `(warm fallback)` are optional.

### benches

- `rg-0023` [Red Bench.JPG](https://commons.wikimedia.org/wiki/File:Red_Bench.JPG)
- `rg-0024` [Red bench on a slope (20333299696).jpg](https://commons.wikimedia.org/wiki/File:Red_bench_on_a_slope_(20333299696).jpg)
- `rg-0025` [Brookmill Park, red benches - geograph.org.uk - 4078270.jpg](https://commons.wikimedia.org/wiki/File:Brookmill_Park,_red_benches_-_geograph.org.uk_-_4078270.jpg)
- `rg-0037` [Banc Jardin botanique Bayonne.JPG](https://commons.wikimedia.org/wiki/File:Banc_Jardin_botanique_Bayonne.JPG)
- `rg-0038` [Eyrignac Manor-red bench.JPG](https://commons.wikimedia.org/wiki/File:Eyrignac_Manor-red_bench.JPG)
- `rg-0039` [Bench in Bruno-Kreisky-Park 03.jpg](https://commons.wikimedia.org/wiki/File:Bench_in_Bruno-Kreisky-Park_03.jpg)
- `rg-0040` [Beautiful People's Pond.jpg](https://commons.wikimedia.org/wiki/File:Beautiful_People%27s_Pond.jpg)
- `rg-0041` [Pamplona - Parque de la Media Luna 01.jpg](https://commons.wikimedia.org/wiki/File:Pamplona_-_Parque_de_la_Media_Luna_01.jpg)
- `rg-0042` [Red Bench in Lumbini, Nepal-IMG 7308.jpg](https://commons.wikimedia.org/wiki/File:Red_Bench_in_Lumbini,_Nepal-IMG_7308.jpg)
- `rg-0043` [Red curved benches with Angsana trees near the Singapore Marriott Tang Plaza tower.jpg](https://commons.wikimedia.org/wiki/File:Red_curved_benches_with_Angsana_trees_near_the_Singapore_Marriott_Tang_Plaza_tower.jpg)
- `rg-0044` [Red bench (7932110410).jpg](https://commons.wikimedia.org/wiki/File:Red_bench_(7932110410).jpg)
- `rg-0045` [Red bench - 4 October 2026.jpg](https://commons.wikimedia.org/wiki/File:Red_bench_-_4_October_2026.jpg)
- `rg-0046` [Remich, banc rouge.jpg](https://commons.wikimedia.org/wiki/File:Remich,_banc_rouge.jpg)
- `rg-0047` [Street bench - Diergaarde Blijdorp - Rotterdam - Wooden planks painted red.jpg](https://commons.wikimedia.org/wiki/File:Street_bench_-_Diergaarde_Blijdorp_-_Rotterdam_-_Wooden_planks_painted_red.jpg)
- `rg-0048` [Traklpark 01.jpg](https://commons.wikimedia.org/wiki/File:Traklpark_01.jpg)
- `rg-0049` [Red benches at Jardim do Coreto, Praça Doutor António Padinha, Tavira, Portugal julesvernex2.jpg](https://commons.wikimedia.org/wiki/File:Red_benches_at_Jardim_do_Coreto,_Pra%C3%A7a_Doutor_Ant%C3%B3nio_Padinha,_Tavira,_Portugal_julesvernex2.jpg)
- `rg-0050` [Banc, allée de l'hôpital, Vichy (2).jpg](https://commons.wikimedia.org/wiki/File:Banc,_all%C3%A9e_de_l%27h%C3%B4pital,_Vichy_(2).jpg)

### berries

- `rg-0077` [Autumn berries (265928588).jpg](https://commons.wikimedia.org/wiki/File:Autumn_berries_(265928588).jpg)
- `rg-0078` [Berries (27777762569).jpg](https://commons.wikimedia.org/wiki/File:Berries_(27777762569).jpg)
- `rg-0079` [Berries (32181806685).jpg](https://commons.wikimedia.org/wiki/File:Berries_(32181806685).jpg)
- `rg-0080` [Berries in Birds Hill Provincial Park, Manitoba. (48895362927).jpg](https://commons.wikimedia.org/wiki/File:Berries_in_Birds_Hill_Provincial_Park,_Manitoba._(48895362927).jpg)
- `rg-0081` [Berries of Canaan Valley 2021a.jpg](https://commons.wikimedia.org/wiki/File:Berries_of_Canaan_Valley_2021a.jpg)
- `rg-0082` [Berry Bush Bonanza (49598285577).jpg](https://commons.wikimedia.org/wiki/File:Berry_Bush_Bonanza_(49598285577).jpg)
- `rg-0083` [Bessen in Bielefeld 2024.jpg](https://commons.wikimedia.org/wiki/File:Bessen_in_Bielefeld_2024.jpg)
- `rg-0084` [Canada Dogwood with berries (d592ef6d-6abb-4668-b9ab-f228db9b84f3).JPG](https://commons.wikimedia.org/wiki/File:Canada_Dogwood_with_berries_(d592ef6d-6abb-4668-b9ab-f228db9b84f3).JPG)
- `rg-0085` [Firethorn Pyracantha Wolves Lane Wood Green London England 01.jpg](https://commons.wikimedia.org/wiki/File:Firethorn_Pyracantha_Wolves_Lane_Wood_Green_London_England_01.jpg)
- `rg-0086` [Bayberry (14293533218).jpg](https://commons.wikimedia.org/wiki/File:Bayberry_(14293533218).jpg)
- `rg-0087` [Andrew Walton 2016 (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Andrew_Walton_2016_(Unsplash).jpg)
- `rg-0088` [Baldwin Wallace Tree with Berries (10240439473).jpg](https://commons.wikimedia.org/wiki/File:Baldwin_Wallace_Tree_with_Berries_(10240439473).jpg)

### bicycles

- `rg-0051` [5.5.2 bike garden setting 4057 05152012 1.jpg](https://commons.wikimedia.org/wiki/File:5.5.2_bike_garden_setting_4057_05152012_1.jpg)
- `rg-0052` [Bicycle & village road.jpg](https://commons.wikimedia.org/wiki/File:Bicycle_%26_village_road.jpg)
- `rg-0053` [Bicycle in Sri Lanka 2023-11-08.jpg](https://commons.wikimedia.org/wiki/File:Bicycle_in_Sri_Lanka_2023-11-08.jpg)
- `rg-0054` [Angeschlossenes, altes, rotes Fahrrad.jpg](https://commons.wikimedia.org/wiki/File:Angeschlossenes,_altes,_rotes_Fahrrad.jpg)
- `rg-0055` [2018-04-29-Altes Fahrrad Durbuy-8593.jpg](https://commons.wikimedia.org/wiki/File:2018-04-29-Altes_Fahrrad_Durbuy-8593.jpg)
- `rg-0056` [Red bicycle (27478994856).jpg](https://commons.wikimedia.org/wiki/File:Red_bicycle_(27478994856).jpg)
- `rg-0057` [Red Bike, Kalamazoo, Michigan.JPG](https://commons.wikimedia.org/wiki/File:Red_Bike,_Kalamazoo,_Michigan.JPG)

### built-other

- `rg-0031` [Green grass meets red steel.jpg](https://commons.wikimedia.org/wiki/File:Green_grass_meets_red_steel.jpg)
- `rg-0032` [HK Admiralty Tamar Park red sculpture Key in art white flowers green plant Sept-2012.JPG](https://commons.wikimedia.org/wiki/File:HK_Admiralty_Tamar_Park_red_sculpture_Key_in_art_white_flowers_green_plant_Sept-2012.JPG)
- `rg-0033` [Red mailbox (1106765119).jpg](https://commons.wikimedia.org/wiki/File:Red_mailbox_(1106765119).jpg)
- `rg-0034` [Red mailbox in South Korea.jpg](https://commons.wikimedia.org/wiki/File:Red_mailbox_in_South_Korea.jpg)
- `rg-0035` [NEILS RED COVERED BRIDGE.jpg](https://commons.wikimedia.org/wiki/File:NEILS_RED_COVERED_BRIDGE.jpg)
- `rg-0036` [Reflection of Light.jpg](https://commons.wikimedia.org/wiki/File:Reflection_of_Light.jpg)

### chairs

- `rg-0097` [Coffee garden in Muğla (2842621632).jpg](https://commons.wikimedia.org/wiki/File:Coffee_garden_in_Mu%C4%9Fla_(2842621632).jpg)
- `rg-0098` [Descanso no fim de tarde (4997334604).jpg](https://commons.wikimedia.org/wiki/File:Descanso_no_fim_de_tarde_(4997334604).jpg)

### flower

- `rg-0001` [Red flower with green leaves.jpg](https://commons.wikimedia.org/wiki/File:Red_flower_with_green_leaves.jpg)
- `rg-0002` [Red flowers with green leaves.jpg](https://commons.wikimedia.org/wiki/File:Red_flowers_with_green_leaves.jpg)
- `rg-0003` [A Red Flower with a green background and broad leaves.jpg](https://commons.wikimedia.org/wiki/File:A_Red_Flower_with_a_green_background_and_broad_leaves.jpg)
- `rg-0004` [Red flower with green leaves in the grass.jpg](https://commons.wikimedia.org/wiki/File:Red_flower_with_green_leaves_in_the_grass.jpg)
- `rg-0005` [Red and Green in one.jpg](https://commons.wikimedia.org/wiki/File:Red_and_Green_in_one.jpg)
- `rg-0006` [A Hibiscus in Lush Embrace.jpg](https://commons.wikimedia.org/wiki/File:A_Hibiscus_in_Lush_Embrace.jpg)
- `rg-0007` [Crimson Beauty in Bloom.jpg](https://commons.wikimedia.org/wiki/File:Crimson_Beauty_in_Bloom.jpg)
- `rg-0008` [The Graceful Red Hibiscus.jpg](https://commons.wikimedia.org/wiki/File:The_Graceful_Red_Hibiscus.jpg)
- `rg-0009` [DFC 6057 A vibrant red hibiscus in full bloom its delicate petals and yellow-tipped stamen contrasting against lush green foliage.jpg](https://commons.wikimedia.org/wiki/File:DFC_6057_A_vibrant_red_hibiscus_in_full_bloom_its_delicate_petals_and_yellow-tipped_stamen_contrasting_against_lush_green_foliage.jpg)
- `rg-0010` [The field - Flickr - Jon Bunting.jpg](https://commons.wikimedia.org/wiki/File:The_field_-_Flickr_-_Jon_Bunting.jpg)

### fruit-berries

- `rg-0011` [Natural apple.jpg](https://commons.wikimedia.org/wiki/File:Natural_apple.jpg)
- `rg-0012` [2018-09-14 28 Devil's club (Oplopanax horridus) plant near Takeetna, Alaska USA.jpg](https://commons.wikimedia.org/wiki/File:2018-09-14_28_Devil%27s_club_(Oplopanax_horridus)_plant_near_Takeetna,_Alaska_USA.jpg)
- `rg-0013` [A view of Lake Roosevelt (6ca5b353-e862-478a-b503-2a1e78697786).jpg](https://commons.wikimedia.org/wiki/File:A_view_of_Lake_Roosevelt_(6ca5b353-e862-478a-b503-2a1e78697786).jpg)
- `rg-0014` [Tomato harvest - Flickr - judy dean.jpg](https://commons.wikimedia.org/wiki/File:Tomato_harvest_-_Flickr_-_judy_dean.jpg)
- `rg-0015` [Red berries.jpg](https://commons.wikimedia.org/wiki/File:Red_berries.jpg)
- `rg-0016` [Shrubs with red berries.jpg](https://commons.wikimedia.org/wiki/File:Shrubs_with_red_berries.jpg)
- `rg-0017` [Strawberry plants with ripe and unripe fruit growing in a garden.jpg](https://commons.wikimedia.org/wiki/File:Strawberry_plants_with_ripe_and_unripe_fruit_growing_in_a_garden.jpg)
- `rg-0018` [Green leaves of wild strawberry with small red berry on a background of gray stone.jpg](https://commons.wikimedia.org/wiki/File:Green_leaves_of_wild_strawberry_with_small_red_berry_on_a_background_of_gray_stone.jpg)

### fungi

- `rg-0101` [Mycena cf. acicula.jpg](https://commons.wikimedia.org/wiki/File:Mycena_cf._acicula.jpg) *(warm fallback)*
- `rg-0102` [Orange mushroom.jpg](https://commons.wikimedia.org/wiki/File:Orange_mushroom.jpg) *(warm fallback)*

### gates

- `rg-0064` [Brick steps and garden gate Walled Garden at Parham House, West Sussex, England.jpg](https://commons.wikimedia.org/wiki/File:Brick_steps_and_garden_gate_Walled_Garden_at_Parham_House,_West_Sussex,_England.jpg)
- `rg-0065` [A red gate, Millcroft Farm, Hensford Road - geograph.org.uk - 1409133.jpg](https://commons.wikimedia.org/wiki/File:A_red_gate,_Millcroft_Farm,_Hensford_Road_-_geograph.org.uk_-_1409133.jpg)
- `rg-0066` [A very red garden gate - geograph.org.uk - 890009.jpg](https://commons.wikimedia.org/wiki/File:A_very_red_garden_gate_-_geograph.org.uk_-_890009.jpg)
- `rg-0067` [A shrub garden and lawn behind a gate at Theydon Mount Essex England.JPG](https://commons.wikimedia.org/wiki/File:A_shrub_garden_and_lawn_behind_a_gate_at_Theydon_Mount_Essex_England.JPG)
- `rg-0068` [3893. Pskovo - Pechorsky Monastery. Gate to the garden.jpg](https://commons.wikimedia.org/wiki/File:3893._Pskovo_-_Pechorsky_Monastery._Gate_to_the_garden.jpg)
- `rg-0069` [Chateau de la Barge, Grézieu-la-Varenne.jpg](https://commons.wikimedia.org/wiki/File:Chateau_de_la_Barge,_Gr%C3%A9zieu-la-Varenne.jpg)
- `rg-0070` [Coldwood - geograph.org.uk - 1263958.jpg](https://commons.wikimedia.org/wiki/File:Coldwood_-_geograph.org.uk_-_1263958.jpg)
- `rg-0071` [Casa da Mainha (1).jpg](https://commons.wikimedia.org/wiki/File:Casa_da_Mainha_(1).jpg)
- `rg-0072` [Field with Red Gate - geograph.org.uk - 134360.jpg](https://commons.wikimedia.org/wiki/File:Field_with_Red_Gate_-_geograph.org.uk_-_134360.jpg)
- `rg-0073` [Red Gate and Tree - geograph.org.uk - 293541.jpg](https://commons.wikimedia.org/wiki/File:Red_Gate_and_Tree_-_geograph.org.uk_-_293541.jpg)
- `rg-0074` [Common grape vine (Vitis vinifera) over a gate with peeling red paint, Beirã, Portugal julesvernex2.jpg](https://commons.wikimedia.org/wiki/File:Common_grape_vine_(Vitis_vinifera)_over_a_gate_with_peeling_red_paint,_Beir%C3%A3,_Portugal_julesvernex2.jpg)
- `rg-0075` [Red Gate Farm - geograph.org.uk - 34940.jpg](https://commons.wikimedia.org/wiki/File:Red_Gate_Farm_-_geograph.org.uk_-_34940.jpg)
- `rg-0076` [Pasture at Ysgubor-wen - geograph.org.uk - 994740.jpg](https://commons.wikimedia.org/wiki/File:Pasture_at_Ysgubor-wen_-_geograph.org.uk_-_994740.jpg)

### green-red-objects

- `rg-0099` [2023-06-04 15 54 20 Green and red fire hydrant at the southeast end of Westwood Drive in the Mountainview section of Ewing Township, Mercer County, New Jersey.jpg](https://commons.wikimedia.org/wiki/File:2023-06-04_15_54_20_Green_and_red_fire_hydrant_at_the_southeast_end_of_Westwood_Drive_in_the_Mountainview_section_of_Ewing_Township,_Mercer_County,_New_Jersey.jpg)
- `rg-0100` [2015 Madeira Samsung (182).jpg](https://commons.wikimedia.org/wiki/File:2015_Madeira_Samsung_(182).jpg)

### insects

- `rg-0019` [Red dragonfly on a leaf.jpg](https://commons.wikimedia.org/wiki/File:Red_dragonfly_on_a_leaf.jpg)
- `rg-0020` [Dragonfly on a leaf.jpg](https://commons.wikimedia.org/wiki/File:Dragonfly_on_a_leaf.jpg)
- `rg-0021` [Ladybird on leaf.jpg](https://commons.wikimedia.org/wiki/File:Ladybird_on_leaf.jpg)
- `rg-0022` [Ladybut on a leaf.jpg](https://commons.wikimedia.org/wiki/File:Ladybut_on_a_leaf.jpg)

### mailboxes

- `rg-0093` [Sjöbergen-koloniområde7.jpg](https://commons.wikimedia.org/wiki/File:Sj%C3%B6bergen-koloniomr%C3%A5de7.jpg)
- `rg-0094` [House on Ockham Lane, Ockham, Surrey (6501165215).jpg](https://commons.wikimedia.org/wiki/File:House_on_Ockham_Lane,_Ockham,_Surrey_(6501165215).jpg)
- `rg-0095` [Rød postkasse.jpg](https://commons.wikimedia.org/wiki/File:R%C3%B8d_postkasse.jpg)
- `rg-0096` [Solidaris mailbox, Uitbergen, 2022.jpg](https://commons.wikimedia.org/wiki/File:Solidaris_mailbox,_Uitbergen,_2022.jpg)

### safety-equipment

- `rg-0103` [DFC 6026 A quiet walkway over water leads into a shaded leafy tunnel - a lifebuoy hangs ready at the railing.jpg](https://commons.wikimedia.org/wiki/File:DFC_6026_A_quiet_walkway_over_water_leads_into_a_shaded_leafy_tunnel_-_a_lifebuoy_hangs_ready_at_the_railing.jpg) *(warm fallback)*
- `rg-0104` [A lifebuoy at Lauder golf course - geograph.org.uk - 897749.jpg](https://commons.wikimedia.org/wiki/File:A_lifebuoy_at_Lauder_golf_course_-_geograph.org.uk_-_897749.jpg) *(warm fallback)*
- `rg-0105` [Lifebuoy at Chellow Dene (2nd October 2010).jpg](https://commons.wikimedia.org/wiki/File:Lifebuoy_at_Chellow_Dene_(2nd_October_2010).jpg) *(warm fallback)*
- `rg-0106` [Beaufort Hill Woodland, Southern Reservoir - geograph.org.uk - 579083.jpg](https://commons.wikimedia.org/wiki/File:Beaufort_Hill_Woodland,_Southern_Reservoir_-_geograph.org.uk_-_579083.jpg) *(warm fallback)*
- `rg-0107` [Lifebuoy, Castle Semple Loch - geograph.org.uk - 582263.jpg](https://commons.wikimedia.org/wiki/File:Lifebuoy,_Castle_Semple_Loch_-_geograph.org.uk_-_582263.jpg) *(warm fallback)*

### tents

- `rg-0058` [-mypubliclandsroadtrip 2016- Our Camping Picks, Wisconsin Islands (27818718472).jpg](https://commons.wikimedia.org/wiki/File:-mypubliclandsroadtrip_2016-_Our_Camping_Picks,_Wisconsin_Islands_(27818718472).jpg)
- `rg-0059` [A tent set in a Kuroyuri-taira, Japan, Summer, 2004.jpg](https://commons.wikimedia.org/wiki/File:A_tent_set_in_a_Kuroyuri-taira,_Japan,_Summer,_2004.jpg)
- `rg-0060` [Campsite at Mystic Beach, Vancouver Island, Canada.jpg](https://commons.wikimedia.org/wiki/File:Campsite_at_Mystic_Beach,_Vancouver_Island,_Canada.jpg)
- `rg-0061` [Emplacement camping nature.jpg](https://commons.wikimedia.org/wiki/File:Emplacement_camping_nature.jpg)
- `rg-0062` [Hilleberg Anaris two person ridge tent.jpg](https://commons.wikimedia.org/wiki/File:Hilleberg_Anaris_two_person_ridge_tent.jpg)
- `rg-0063` [Naturpark Gantrisch 017.jpg](https://commons.wikimedia.org/wiki/File:Naturpark_Gantrisch_017.jpg)

### umbrellas

- `rg-0089` [Radlett Cricket Club pavilion, Hertfordshire 1.jpg](https://commons.wikimedia.org/wiki/File:Radlett_Cricket_Club_pavilion,_Hertfordshire_1.jpg)
- `rg-0090` [Red Umbrella (14428439970).jpg](https://commons.wikimedia.org/wiki/File:Red_Umbrella_(14428439970).jpg)
- `rg-0091` [Red red (on explore at July 16, 2025) - Flickr - Sandor Somkuti.jpg](https://commons.wikimedia.org/wiki/File:Red_red_(on_explore_at_July_16,_2025)_-_Flickr_-_Sandor_Somkuti.jpg)
- `rg-0092` [Ratargul Md. Akhlas Uddin 1.jpg](https://commons.wikimedia.org/wiki/File:Ratargul_Md._Akhlas_Uddin_1.jpg)

### vehicles-machinery

- `rg-0026` [Old red tractor parked on a dirt road surrounded by greenery.jpg](https://commons.wikimedia.org/wiki/File:Old_red_tractor_parked_on_a_dirt_road_surrounded_by_greenery.jpg)
- `rg-0027` [Old rusty tractor parked in a serene field.jpg](https://commons.wikimedia.org/wiki/File:Old_rusty_tractor_parked_in_a_serene_field.jpg)
- `rg-0028` [Red Tractor.jpg](https://commons.wikimedia.org/wiki/File:Red_Tractor.jpg)
- `rg-0029` [Carro Antiguo en la Antigua Pista de caballos de club Hipódromo de la Colonia Condesa, Ciudad de México.jpg](https://commons.wikimedia.org/wiki/File:Carro_Antiguo_en_la_Antigua_Pista_de_caballos_de_club_Hip%C3%B3dromo_de_la_Colonia_Condesa,_Ciudad_de_M%C3%A9xico.jpg)
- `rg-0030` [Casas de Plaza Río de Janeiro en la Ciudad de México.jpg](https://commons.wikimedia.org/wiki/File:Casas_de_Plaza_R%C3%ADo_de_Janeiro_en_la_Ciudad_de_M%C3%A9xico.jpg)

