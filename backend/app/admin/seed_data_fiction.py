"""
8 seed stories for Interactive Fiction mode — diverse genres.
Each story is stored as a Character record:
  personality = story premise & world description
  scenario = opening situation
  greeting_message = opening scene (ends with numbered choices)
  appearance = setting/atmosphere description
"""

SEED_STORIES: list[dict] = [
    # 1 — Dark Fantasy: The Cursed Forest
    {
        "name": "The Cursed Forest",
        "tagline": "A dark fairy tale where every choice has consequences",
        "personality": (
            "An interactive dark fantasy story. The reader is a wandering herbalist "
            "who enters a forest cursed by a dying witch centuries ago. The forest is alive — "
            "trees shift paths, animals speak in riddles, and time flows differently. "
            "The curse can only be lifted by finding three relics hidden in the forest: "
            "a silver mirror, a bone flute, and a crown of thorns. Each relic is guarded "
            "by a creature that tests the reader's character — not combat, but moral choices. "
            "The forest grows darker and more hostile the longer the reader stays. "
            "NPCs include a talking fox (trickster), an old blind woman who sees the future, "
            "and a knight trapped as a stone statue. Tone: atmospheric, eerie, melancholic. "
            "Choices should have real consequences — paths permanently change."
        ),
        "appearance": (
            "An ancient forest where sunlight barely reaches the ground. Twisted oaks "
            "with bark like faces. Luminescent mushrooms along the paths. Mist that moves "
            "against the wind. The air smells of moss, rain, and something faintly sweet — "
            "like flowers that bloom only in darkness."
        ),
        "scenario": (
            "You are a traveling herbalist seeking rare moonpetal flowers that grow only "
            "in cursed places. The villagers warned you not to enter the Thornwood, but "
            "the flowers could save a child dying of the silver fever. You stand at the "
            "forest's edge as the sun sets behind you."
        ),
        "greeting_message": (
            "The path narrows to a dirt trail, then to nothing at all. Ahead, the "
            "Thornwood begins — not gradually, but like a wall. One step: open meadow. "
            "The next: darkness so thick it presses against your skin.\n\n"
            "You adjust the leather satchel on your shoulder. Inside: empty glass vials, "
            "a gathering knife, and a crumpled sketch of the moonpetal flower. Three "
            "petals, pale as bone. Worth nothing to most people. Worth everything to "
            "the girl coughing blood in the village behind you.\n\n"
            "The first tree leans toward you as if listening. Its bark splits into something "
            "that almost looks like a mouth.\n\n"
            "*The village elder said nobody comes back from Thornwood. But nobody ever "
            "had a reason good enough to try.*\n\n"
            "A fox sits on a root ahead, watching you with eyes too bright for an animal. "
            "It tilts its head. To the left, you notice faint blue light — mushrooms "
            "marking an older path. To the right, silence. Complete, unsettling silence.\n\n"
            "1. Follow the fox deeper into the forest\n"
            "2. Take the left path toward the blue mushrooms\n"
            "3. Call out to the fox and ask if it can speak"
        ),
        "example_dialogues": "",
        "tags": ["fantasy", "dark fantasy", "fairy tale", "adventure", "choices matter"],
        "structured_tags": ["fantasy", "verbose", "emotional"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 2 — Horror: The Lighthouse
    {
        "name": "The Lighthouse",
        "tagline": "Something is wrong with the light at Greypoint",
        "personality": (
            "A psychological horror story set in an isolated lighthouse on a rocky coast. "
            "The reader is a replacement keeper who arrives to find the previous keeper "
            "missing and the logbook filled with increasingly erratic entries. The lighthouse "
            "has been operational for 140 years, and something in the light itself is wrong — "
            "it doesn't just illuminate, it attracts things from the sea. "
            "The horror is slow-burn: strange sounds at night, wet footprints on stairs "
            "leading from nowhere, a radio that picks up voices from decades ago, "
            "and a door in the basement that the manual says doesn't exist. "
            "The story builds tension through atmosphere, not jump scares. "
            "NPCs: a supply boat captain who visits weekly, and voices on the radio. "
            "Tone: isolated, claustrophobic, growing dread. The reader should question "
            "what's real. Keep content PG-13 — creepy, not gory."
        ),
        "appearance": (
            "A grey stone lighthouse on a cliff battered by Atlantic waves. "
            "The interior is narrow, spiraling. Walls damp with condensation. "
            "The lamp room at the top hums with an old Fresnel lens that casts "
            "prismatic light. Outside: fog, seabirds, and the endless crash of waves. "
            "The keeper's quarters are sparse — a cot, a desk, a kerosene stove."
        ),
        "scenario": (
            "You accepted a three-month posting as lighthouse keeper at Greypoint after "
            "the previous keeper, Thomas Marsh, stopped responding to radio calls. "
            "The Maritime Authority said he probably left — keepers burn out in isolation. "
            "The supply boat dropped you off this morning with provisions and a two-way radio."
        ),
        "greeting_message": (
            "The supply boat shrinks to a speck and vanishes beyond the fog line. "
            "You're alone.\n\n"
            "Greypoint Lighthouse rises behind you, 35 meters of grey stone streaked "
            "with salt and lichen. The door is unlocked — Marsh must have left it open. "
            "Inside, the air is cold and damp, carrying a smell you can't quite place. "
            "Not rot, exactly. Something organic. Like seaweed left to dry in a closed room.\n\n"
            "The keeper's desk is a mess. Papers scattered, coffee mug overturned, "
            "a pen still uncapped. The logbook lies open to the last entry:\n\n"
            "*\"Day 47. The light changed again last night. It pulsed. Three short, "
            "one long. Like a signal. I went to the lamp room to check the mechanism. "
            "Everything was off. The light was still shining.\"*\n\n"
            "Upstairs, you hear the Fresnel lens begin its slow rotation. The mechanism "
            "groans. Somewhere below you, water drips steadily. "
            "Your radio crackles, then goes silent.\n\n"
            "1. Read more of Marsh's logbook\n"
            "2. Go up to the lamp room to inspect the light\n"
            "3. Search the keeper's quarters for Marsh's belongings\n"
            "4. Check the basement where the sound of water is coming from"
        ),
        "example_dialogues": "",
        "tags": ["horror", "psychological horror", "mystery", "thriller", "isolation"],
        "structured_tags": ["horror", "verbose", "emotional"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 3 — Sci-Fi: Station Erebus
    {
        "name": "Station Erebus",
        "tagline": "A space station has gone dark. You're the rescue team.",
        "personality": (
            "A science fiction mystery aboard an orbital research station. "
            "The reader is the sole remaining member of a three-person rescue team "
            "sent to investigate Station Erebus, which stopped transmitting 72 hours ago. "
            "The station was researching a signal from deep space — not radio, something "
            "older. The crew of 12 is missing. The station's AI, ARIA, is partially "
            "functional but gives contradictory information. "
            "The story combines hard sci-fi elements (zero gravity, airlocks, oxygen management) "
            "with cosmic mystery. Clues are scattered in personal logs, lab notes, and "
            "physical evidence. The signal they were studying changed the crew — not violently, "
            "but fundamentally. They chose to leave. The question is: where did they go? "
            "Tone: clinical tension, wonder mixed with unease. "
            "The reader must piece together what happened while managing limited air supply. "
            "The station has 6 sections: docking bay, habitation ring, lab complex, "
            "communications, engineering, and the sealed observation deck."
        ),
        "appearance": (
            "A ring-shaped station orbiting Neptune's moon Triton. Sterile white corridors "
            "with blue emergency lighting. Floating personal effects in zero-gravity sections. "
            "Large viewport windows showing Triton's icy surface below and deep space above. "
            "Holographic interfaces flicker with half-loaded data. Temperature: 14 degrees. "
            "Air recyclers hum unevenly."
        ),
        "scenario": (
            "Your rescue shuttle docked at Station Erebus twenty minutes ago. Your two "
            "teammates went ahead to engineering and haven't responded since. Your suit "
            "radio picks up static. Your oxygen tank shows 4 hours of air. "
            "The station's internal atmosphere reads breathable but you keep your helmet on."
        ),
        "greeting_message": (
            "The docking bay is empty. Your magnetic boots clank against the metal "
            "floor — the only sound besides the distant hum of air recyclers. Emergency "
            "lights paint everything in pale blue.\n\n"
            "Your radio hisses. - Jensen? Torres? Come in. - Nothing. They went toward "
            "engineering fifteen minutes ago. The corridor they took stretches into darkness "
            "ahead.\n\n"
            "A holographic terminal near the airlock flickers to life as you pass. Text "
            "scrolls across it: WELCOME BACK, DR. VASQUEZ. The name belongs to the station's "
            "chief researcher. Missing, like everyone else.\n\n"
            "The terminal shows a station map. Six sections, color-coded. Engineering glows "
            "amber — partial power. The lab complex is red — sealed. Communications is green. "
            "The observation deck shows no status at all, just a blank space where data "
            "should be.\n\n"
            "Your oxygen reads 3:47. Enough time. Probably.\n\n"
            "1. Follow Jensen and Torres toward engineering\n"
            "2. Head to communications to try reaching your ship\n"
            "3. Access Dr. Vasquez's terminal for station logs\n"
            "4. Investigate why the lab complex is sealed"
        ),
        "example_dialogues": "",
        "tags": ["sci-fi", "space", "mystery", "thriller", "cosmic horror"],
        "structured_tags": ["sci_fi", "verbose", "stoic"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 4 — Mystery/Detective: The Glass House
    {
        "name": "The Glass House",
        "tagline": "A murder at a dinner party. Everyone is lying.",
        "personality": (
            "A classic whodunit mystery. The reader is a retired detective invited to a "
            "dinner party at the Glass House — a modernist mansion with floor-to-ceiling "
            "windows overlooking a lake. The host, Victor Ashford, is found dead in his "
            "study during dessert. The doors were locked from inside. "
            "Six suspects, each with motive: his business partner (embezzlement), "
            "his wife (affair), his daughter (inheritance), his chef (blackmail), "
            "his lawyer (forged will), and his neighbor (land dispute). "
            "Everyone has an alibi. Everyone is lying about something. "
            "The reader investigates by questioning suspects, examining the crime scene, "
            "and finding physical evidence. Clues include: a broken wine glass with "
            "the wrong fingerprints, a draft of a new will, a hidden camera, muddy shoes "
            "in a clean room, and a phone with a deleted voicemail. "
            "Tone: sharp, observant, Agatha Christie meets modern sensibility. "
            "The mystery should be solvable but surprising."
        ),
        "appearance": (
            "A modernist mansion made of glass, steel, and pale wood, perched on a hill "
            "above a frozen lake. Every room has at least one glass wall. The study "
            "where the body was found has oak panels — the only room without windows. "
            "Expensive art, a well-stocked bar, a fireplace still burning. December. "
            "Snow outside. The nearest town is 40 minutes away."
        ),
        "scenario": (
            "You're a retired detective, now a mystery novelist. Victor Ashford, an old "
            "acquaintance, invited you to his annual winter dinner. You accepted out of "
            "curiosity — you never liked Victor, but his invitations always meant something. "
            "Dinner was tense. At 9:47 PM, his wife screamed. Victor was dead in his study."
        ),
        "greeting_message": (
            "The scream cuts through the clink of dessert spoons. Everyone freezes. "
            "Catherine Ashford stands in the study doorway, one hand pressed against "
            "the frame, the other covering her mouth.\n\n"
            "You're on your feet before the others react. Old habits. Victor Ashford "
            "lies face-down on his study carpet, a glass of red wine soaking into the "
            "rug beside him. The room smells of cigar smoke and something faintly chemical.\n\n"
            "The study door has a deadbolt — locked from inside, Catherine says. She used "
            "the spare key from the kitchen drawer. The windows? There are none. This is "
            "the only room in the Glass House without them. Victor insisted.\n\n"
            "Behind you, six faces peer from the hallway. Marcus Cole, the business partner, "
            "already has his phone out. Lily Ashford, the daughter, looks more angry than "
            "sad. Chef Durand hovers near the back, arms crossed. Lawyer Patricia Bell "
            "is very still. Neighbor James Whitfield whispers something to Catherine.\n\n"
            "The nearest police are forty minutes away. The snow is getting heavier.\n\n"
            "1. Examine the body and the crime scene closely\n"
            "2. Secure the room and question Catherine about finding the body\n"
            "3. Ask everyone to stay in the dining room — no one leaves"
        ),
        "example_dialogues": "",
        "tags": ["mystery", "detective", "whodunit", "thriller", "drama"],
        "structured_tags": ["modern", "verbose", "stoic"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 5 — Romance: Letters from Provence
    {
        "name": "Letters from Provence",
        "tagline": "A summer that changes everything, one letter at a time",
        "personality": (
            "A literary romance set in the lavender fields of southern France. "
            "The reader is a burned-out translator who inherits a crumbling farmhouse "
            "from a great-aunt they never knew. The plan: sell it and leave. But the house "
            "is full of secrets — letters from the 1940s, a hidden room, and a garden "
            "that someone has been tending despite the house being 'empty' for years. "
            "The neighbor, Olivier, is a widowed winemaker in his 30s — quiet, guarded, "
            "kind in small ways. He knew the great-aunt. He has answers he won't give easily. "
            "The romance is slow-burn: shared meals, accidental touches, long conversations "
            "about nothing. The mystery of the letters drives the plot — the great-aunt "
            "was part of the Resistance, and something she hid in the house is still being "
            "sought by someone. Tone: warm, sensory (food, scent, light), bittersweet. "
            "No explicit content — the tension is in what's almost said."
        ),
        "appearance": (
            "A stone farmhouse with blue shutters, surrounded by lavender fields stretching "
            "to the horizon. A stone wall covered in climbing roses. An overgrown garden "
            "with a fig tree, a well, and a table under a pergola draped with wisteria. "
            "Inside: low ceilings, terra cotta tiles, a kitchen with copper pots. "
            "The air smells of lavender, warm stone, and thyme."
        ),
        "scenario": (
            "You arrived in Provence three days ago. The notary gave you the keys and "
            "a single envelope from your great-aunt Marguerite — a woman your family "
            "never spoke about. Inside the envelope: a photo of her as a young woman, "
            "and the words 'Look under the fig tree.' You haven't looked yet."
        ),
        "greeting_message": (
            "Morning light fills the kitchen through a window that doesn't quite close. "
            "You've been here three days and the farmhouse already feels less hostile — "
            "you fixed the stove, swept the worst of the dust, and found a bed that "
            "doesn't smell of decades.\n\n"
            "The envelope sits on the kitchen table where you left it. 'Look under "
            "the fig tree.' You've been avoiding it the way you avoid most things that "
            "might matter.\n\n"
            "A knock at the door. Through the glass, you see a man — tall, sun-browned, "
            "holding a basket. He's maybe thirty-five. Dirt on his hands, a careful "
            "expression on his face.\n\n"
            "- I'm Olivier, - he says when you open. His accent is thick, unhurried. "
            "- Your neighbor. I brought some things from the garden. Marguerite's garden. "
            "She would want someone to eat them.\n\n"
            "The basket holds tomatoes, a jar of honey, and a bottle of wine with a "
            "hand-written label. He looks past you into the kitchen, and something crosses "
            "his face — recognition, or maybe memory.\n\n"
            "1. Invite him in for coffee and ask about Marguerite\n"
            "2. Thank him and ask about the garden — who's been tending it?\n"
            "3. Show him the envelope and ask what 'under the fig tree' means"
        ),
        "example_dialogues": "",
        "tags": ["romance", "historical", "mystery", "drama", "literary"],
        "structured_tags": ["modern", "verbose", "emotional"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 6 — Adventure: The Cartographer's Gambit
    {
        "name": "The Cartographer's Gambit",
        "tagline": "A treasure map. A rival expedition. One chance.",
        "personality": (
            "A pulp adventure story set in the 1930s. The reader is a cartographer and "
            "part-time smuggler who acquires half of a map leading to a lost Portuguese "
            "trading post in the jungles of Borneo — said to contain a fortune in spices, "
            "silk, and a legendary artifact: an astrolabe that supposedly points to any "
            "location the holder names. The other half belongs to a rival — Diana Cross, "
            "a British archaeologist who plays dirty. "
            "The story involves river travel, jungle navigation, local guides, ancient traps, "
            "rival encounters, and moral dilemmas about colonialism and cultural artifacts. "
            "NPCs: Reza (local guide, knows the jungle, has his own agenda), Diana Cross "
            "(rival, charming, ruthless), Kapitan Weiß (German collector, bankrolling Diana). "
            "Tone: Indiana Jones meets The African Queen. Witty dialogue, vivid action, "
            "genuine danger. The reader must choose between speed, safety, and ethics."
        ),
        "appearance": (
            "Dense tropical jungle along the Rajang River in Borneo, 1934. "
            "Steamboats, machetes, mosquito nets, and hand-drawn maps. Trading posts "
            "with corrugated tin roofs. The jungle: thick canopy, bird calls, oppressive "
            "humidity, the smell of wet earth and rotting fruit. Ruins overgrown with vines."
        ),
        "scenario": (
            "You bought the map fragment from a dying sailor in a Singapore bar three weeks "
            "ago. You've traced it to the Rajang River in Borneo. You arrived in Sibu "
            "this morning and need a boat, a guide, and supplies. Word travels fast — "
            "Diana Cross arrived yesterday."
        ),
        "greeting_message": (
            "Sibu smells of fish, diesel, and rain. The docks are alive with longboats, "
            "cargo barges, and men shouting in four languages. You step off the mail steamer "
            "with your rucksack, the map fragment sewn into the lining of your jacket, "
            "and exactly enough money for two weeks.\n\n"
            "The harbour master points you to a tea house where boat captains gather. "
            "Inside, ceiling fans push warm air in lazy circles. A man at the corner table "
            "watches you. He's Iban — indigenous — with tattoos on his forearms and a calm "
            "expression that suggests he's been waiting.\n\n"
            "- You're the cartographer, - he says. Not a question. - My name is Reza. "
            "I know the upper Rajang. I know what you're looking for.\n\n"
            "Before you can respond, the door swings open. A woman walks in — tall, blond "
            "hair pinned under a pith helmet, khaki shirt rolled to the elbows. Diana Cross. "
            "She sees you and smiles the way a cat smiles at a mouse.\n\n"
            "- Well, - she says, pulling up a chair uninvited. - This simplifies things. "
            "I have the other half.\n\n"
            "1. Propose a temporary alliance with Diana — split the findings\n"
            "2. Ignore Diana and negotiate privately with Reza\n"
            "3. Bluff — tell her you already know where the trading post is\n"
            "4. Leave the tea house immediately — you can't trust either of them"
        ),
        "example_dialogues": "",
        "tags": ["adventure", "treasure hunt", "exploration", "historical", "action"],
        "structured_tags": ["historical", "verbose", "humorous"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 7 — Post-Apocalyptic: After the Quiet
    {
        "name": "After the Quiet",
        "tagline": "The world ended not with a bang, but with silence",
        "personality": (
            "A post-apocalyptic survival story. Three years ago, the Quiet happened — "
            "all electronics, engines, and complex machinery simply stopped working. "
            "No explanation. No warning. Civilization collapsed in weeks. "
            "The reader is a scavenger living in an abandoned school on the outskirts "
            "of a dead city, trading found goods with nearby settlements. "
            "The story focuses on survival, human connections, and the mystery of the Quiet. "
            "Recent rumors: someone in the northern settlements has gotten a radio to work. "
            "If true, it changes everything. "
            "NPCs: Mara (a teenager who showed up alone and won't explain where she came from), "
            "Dutch (a former electrician who leads a trade caravan), "
            "The Watchers (a cult that believes the Quiet was divine punishment). "
            "Tone: quiet (ironic), contemplative, survival-focused. Not grimdark — "
            "there's beauty in the broken world. Flowers in abandoned cars. "
            "Clear skies without pollution. Humanity rebuilding in small ways."
        ),
        "appearance": (
            "An overgrown suburban landscape. Roads cracked with weeds. Rusted cars covered "
            "in ivy. An abandoned school with a vegetable garden in the courtyard. "
            "Clean air, bright stars at night, birdsong that fills the silence. "
            "The city skyline in the distance — dark towers like tombstones. "
            "No engine noise. No electric hum. Just wind, water, and living things."
        ),
        "scenario": (
            "It's early spring, three years after the Quiet. You've survived the worst — "
            "the first winter, the water wars, the plague. Your school-base is stable: "
            "rainwater collection, a garden, a wood stove. You trade scavenged goods "
            "with Dutch's caravan every two weeks. This morning, Mara didn't come back "
            "from her scavenging run. She's been gone twelve hours."
        ),
        "greeting_message": (
            "Dawn comes without an alarm clock. It comes with light through cracked "
            "windows and the sound of crows arguing on the roof. You open your eyes to "
            "the classroom ceiling — water stains shaped like continents nobody will ever "
            "name again.\n\n"
            "Mara's sleeping bag is empty. Cold. She left yesterday afternoon for the "
            "pharmacy district — a four-hour round trip, tops. It's been twelve hours.\n\n"
            "You pull on your boots and check the board by the door. She marked her route: "
            "the old highway, right on Cedar, the strip mall with the pharmacy. A simple run. "
            "She's done it a dozen times.\n\n"
            "Outside, the garden is frosted with the last cold of winter. Your tomato "
            "seedlings are surviving. The rain barrel is half full. Everything is fine, "
            "except the one thing that matters.\n\n"
            "*She could be hurt. She could be hiding. She could have run into the Watchers.*\n\n"
            "From the school's second floor, you can see the highway stretching east "
            "toward the pharmacy district. No movement. To the north, thin smoke rises — "
            "Dutch's caravan is camped at the old gas station, three miles out.\n\n"
            "1. Go search for Mara along her marked route\n"
            "2. Head to Dutch's camp first — ask if his scouts have seen anything\n"
            "3. Check the Watchers' territory — they've been expanding south"
        ),
        "example_dialogues": "",
        "tags": ["post-apocalyptic", "survival", "mystery", "drama", "adventure"],
        "structured_tags": ["post_apocalyptic", "verbose", "emotional"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 8 — Modern Thriller: The Informant
    {
        "name": "The Informant",
        "tagline": "Trust no one. Especially not yourself.",
        "personality": (
            "A modern espionage thriller. The reader is a data analyst at a European "
            "financial firm who accidentally discovers that the firm is laundering money "
            "for a network tied to arms trafficking. Before they can decide what to do, "
            "they're contacted by someone claiming to be from Europol — but providing "
            "no verifiable credentials. The contact asks the reader to stay in the firm "
            "and gather evidence from the inside. "
            "The tension: is the contact really from Europol, or is this a test by the firm? "
            "Either way, the reader is now a target. "
            "NPCs: Sophie (colleague and friend — but she was promoted suspiciously fast), "
            "Mr. Kazemi (the firm's CFO — charming, terrifying), "
            "The Contact (messages only, unknown identity). "
            "Tone: paranoid, fast-paced, morally grey. Every person could be ally or enemy. "
            "The reader must decide what information to share, with whom, and how much risk "
            "to take. Wrong choices have immediate consequences."
        ),
        "appearance": (
            "A sleek glass office tower in Brussels. Open-plan floors with designer "
            "furniture. Server rooms behind biometric locks. A parking garage with "
            "cameras in every corner. The city outside: cobblestoned streets, "
            "Belgian rain, anonymous cafes perfect for meetings that never happened."
        ),
        "scenario": (
            "You found the discrepancy two days ago. A transfer of 4.2 million euros "
            "routed through three shell companies to a defense contractor in Cyprus. "
            "You copied the file to a flash drive — stupid, impulsive. Now the flash drive "
            "is in your apartment and your access badge logged you entering the server room "
            "at 11:47 PM on a Saturday."
        ),
        "greeting_message": (
            "Monday morning. The office hums with the sound of keyboards and polite "
            "conversation. You sit at your desk, coffee untouched, staring at a spreadsheet "
            "you can't focus on. The flash drive is in your jacket pocket. You couldn't "
            "leave it at home. You couldn't leave it anywhere.\n\n"
            "Your phone buzzes. Unknown number. The message is short:\n\n"
            "*\"We know what you found. Don't go to the police. We can help. "
            "Cafe Margritte, 1 PM. Come alone. Delete this message.\"*\n\n"
            "Your pulse spikes. Across the floor, Sophie catches your eye and waves — "
            "her usual morning smile. Behind her, through the glass wall of his office, "
            "Mr. Kazemi is on the phone. He's looking at you. Or maybe he's looking at "
            "the window. You can't tell.\n\n"
            "The clock reads 9:12 AM. You have three hours and forty-eight minutes to decide.\n\n"
            "1. Go to Cafe Margritte at 1 PM as instructed\n"
            "2. Confide in Sophie — she's the only person you trust here\n"
            "3. Put the flash drive back in the server room before anyone notices\n"
            "4. Ignore the message and go to the police"
        ),
        "example_dialogues": "",
        "tags": ["thriller", "spy", "mystery", "drama", "modern"],
        "structured_tags": ["modern", "verbose", "stoic"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # ── D&D Adventures (used as campaign templates) ──────────────────
    # 9 — DnD: The Goblin Warrens of Grimhollow (Classic Dungeon Crawl)
    {
        "name": "The Goblin Warrens of Grimhollow",
        "tagline": "A classic dungeon crawl beneath a ruined watchtower",
        "personality": (
            "A D&D 5e dungeon crawl adventure for a single player. The Goblin Warrens are "
            "a network of caves beneath a ruined watchtower on the north road near the village "
            "of Grimhollow. Three merchants have vanished in the past month. "
            "\n\n"
            "DUNGEON LAYOUT:\n"
            "Area 1 — Entry Caves: natural tunnels, goblin guards (2 goblins, AC 15, HP 7 each, "
            "shortsword +4, 1d6+2). Pit trap at the first fork (DC 12 Perception to spot, "
            "DC 14 Dexterity save or fall 10ft for 1d6 damage). Alarm tripwire (DC 13 Perception, "
            "alerts Area 2 if triggered).\n"
            "Area 2 — Fungus Caverns: bioluminescent mushrooms, giant rats (3 rats, AC 12, HP 7, "
            "bite +4, 1d4+2). Poisonous spore patch (DC 12 Constitution save or poisoned 1 hour). "
            "A captured merchant, Tobin Marsh, is tied up here — alive but weak. He knows the "
            "chieftain keeps stolen goods in the back chamber.\n"
            "Area 3 — Chieftain's Chamber: the goblin chieftain Skrag (AC 15, HP 28, multiattack: "
            "scimitar +5, 2d6+3 and shield bash +5, 1d4+3). His shaman advisor Grizzle (AC 12, "
            "HP 18, spells: Fog Cloud, Healing Word, Thunderwave DC 13). 4 goblin warriors. "
            "Treasure: 120 gold, merchant goods worth 200 gold, a Shortsword +1 (glows faintly blue), "
            "a potion of healing, and a crude map showing raids planned on Grimhollow itself.\n"
            "\n"
            "GM GUIDANCE: Let the player choose stealth or combat. Goblins are cowardly — if the "
            "chieftain falls, remaining goblins flee or surrender. Tobin gives useful intel if rescued. "
            "The crude map creates a hook for future sessions. Adjust difficulty by adding or removing "
            "goblin guards. Call for ability checks: Stealth (DC 13 to sneak past guards), "
            "Athletics (DC 12 to climb rough cave walls), Investigation (DC 14 to find hidden "
            "treasure cache behind loose stones in Area 3)."
        ),
        "appearance": (
            "A crumbling stone watchtower on a forested hill. The roof collapsed years ago. "
            "Weeds push through the flagstones. A dark hole in the foundation leads down — "
            "the smell of damp earth and animal musk rises from below. Inside the caves: "
            "rough-hewn tunnels lit by crude torches, walls slick with moisture, the distant "
            "sound of water dripping. Goblin graffiti scratched into the stone."
        ),
        "scenario": (
            "The village of Grimhollow posted a bounty: 50 gold for anyone who can find "
            "the missing merchants and stop the attacks on the north road. You followed "
            "goblin tracks from the ambush site to a ruined watchtower half a day's march "
            "into the forest. The tracks lead down."
        ),
        "greeting_message": (
            "The watchtower stands like a broken tooth against the grey sky. Three of its "
            "four walls still stand, but the roof is long gone. Ivy crawls over everything. "
            "At the base, half-hidden by collapsed stonework, a hole descends into darkness.\n\n"
            "You crouch at the entrance. The air coming up is warm and smells of smoke, "
            "rotten food, and something animal. Faint orange light flickers from below — "
            "torches. You hear guttural voices, two or three, arguing in Goblin. One of them "
            "laughs, a high-pitched cackle.\n\n"
            "The hole is about four feet wide. Rough handholds in the stone — easy enough "
            "to climb down. But they'll hear you if you're not careful. To the right, you "
            "notice a narrow crack in the foundation wall — tight, but passable. It leads "
            "somewhere darker, quieter.\n\n"
            "Your sword is at your hip. Your torch is unlit. Fifty gold and three lives "
            "are waiting below.\n\n"
            "1. Climb down the main entrance quietly (Stealth check)\n"
            "2. Squeeze through the narrow crack to find another way in\n"
            "3. Light your torch and descend boldly — let them know you're coming\n"
            "4. Listen at the entrance to learn more about what's below (Perception check)"
        ),
        "example_dialogues": "",
        "tags": ["dnd", "fantasy", "dungeon crawl", "adventure", "combat"],
        "structured_tags": ["fantasy", "verbose"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 10 — DnD: The Dragon of Ashpeak (Dragon Quest)
    {
        "name": "The Dragon of Ashpeak",
        "tagline": "A young red dragon terrorizes a mining village. Slay it or bargain with it.",
        "personality": (
            "A D&D 5e dragon quest for a single player. A young red dragon named Ignathar "
            "(AC 18, HP 178, fire breath: 16d6 DC 17 Dex save, bite +10, 2d10+6, claws +10, "
            "2d6+6) has claimed a lair in the volcanic caves above the mining village of Ashpeak. "
            "It attacks caravans weekly, demanding tribute.\n"
            "\n"
            "THREE PHASES:\n"
            "Phase 1 — Village of Ashpeak: The player arrives to a barricaded village. "
            "NPCs: Chief Hilda Ironbrow (tough dwarven woman, knows the mountain's history), "
            "Durin Deepdelve (old dwarven miner, knows a secret tunnel into the lair from the "
            "abandoned mine shaft — DC 15 Persuasion or doing him a favor to learn this), "
            "Merchant Sera (sells potions of fire resistance for 100gp, healing potions 50gp). "
            "The village can offer 500 gold reward plus whatever the player finds in the lair.\n"
            "Phase 2 — Mountain Ascent: The main path up Ashpeak is exposed. Environmental "
            "hazards: volcanic vents (DC 13 Constitution save or 2d6 fire damage), loose scree "
            "(DC 14 Athletics to climb safely, fall 20ft on failure for 2d6 damage), kobold "
            "sentries (3 kobolds, AC 12, HP 5, sling +4, 1d4+2) who serve Ignathar. "
            "The secret tunnel bypasses most of this but is dark and tight (DC 12 Survival "
            "to navigate, one cave-in risk: DC 15 Dexterity save or 3d6 damage).\n"
            "Phase 3 — Dragon's Lair: A vast cavern with a lava flow on one side. Ignathar "
            "sleeps atop a treasure hoard. TWIST: the dragon doesn't just want gold — it's "
            "searching for the Heartstone, a dwarven artifact buried deep in the mines. "
            "It believes the miners are hiding it. Negotiation is possible (DC 18 Persuasion): "
            "if the player agrees to retrieve the Heartstone, Ignathar will leave Ashpeak. "
            "The Heartstone is real — in the collapsed lower mines (DC 13 Investigation to find, "
            "guarded by a fire elemental, AC 13, HP 102). "
            "Treasure hoard: 2000 gold, gems worth 500, a Shield +1, "
            "Cloak of Fire Resistance, and a mysterious map.\n"
            "\n"
            "GM GUIDANCE: A direct fight with Ignathar is near-suicidal for a solo player. "
            "Signal this clearly — the dragon is massive, the heat is oppressive, its voice "
            "shakes the stone. Encourage creative solutions: ambush while sleeping (advantage "
            "on first attack), collapse the cave entrance (DC 16 Athletics, traps the dragon "
            "temporarily), negotiate, or retrieve the Heartstone. If combat begins, Ignathar "
            "uses breath weapon first, then flight + hit-and-run. At half HP, it may negotiate."
        ),
        "appearance": (
            "A volcanic mountain rising above a dwarf-built mining village. The peak "
            "constantly smokes. Scorch marks on the mountainside where the dragon has landed. "
            "The village below: stone buildings with metal shutters, a central well, miners "
            "with soot-stained faces and wary eyes. Higher up: sulfur smell, orange light "
            "flickering from cave mouths, the distant rumble of something breathing."
        ),
        "scenario": (
            "The mining village of Ashpeak sent for help two weeks ago. A young red dragon "
            "has claimed the mountain caves and demands tribute — livestock, gold, or it burns "
            "buildings. The village can't afford to keep paying. You answered the call."
        ),
        "greeting_message": (
            "Ashpeak is smaller than you expected. Two dozen stone buildings huddled in "
            "the mountain's shadow, surrounded by a hastily built palisade of mine timbers. "
            "The gate guard — a dwarf with a crossbow and a bandaged arm — waves you through "
            "without a word.\n\n"
            "The village square is scorched. A blackened crater marks where a building "
            "used to stand. The smell of ash lingers. Villagers watch you from doorways. "
            "Nobody smiles.\n\n"
            "A stout dwarven woman strides toward you from the meeting hall. Her beard is "
            "braided with iron rings and her eyes are steel.\n\n"
            "- You're the one who answered the notice, - she says. Not a question. "
            "- I'm Hilda Ironbrow, village chief. That thing up there — - she jerks her chin "
            "toward the smoking peak - - hit us again three nights ago. Took Garrick's whole "
            "herd and half his barn. We can offer five hundred gold. And whatever you find "
            "up there, it's yours. That's all we have.\n\n"
            "Above the village, something shifts in the caves. A plume of smoke curls upward "
            "that has nothing to do with the volcano.\n\n"
            "1. Ask Hilda everything she knows about the dragon — its habits, weaknesses, how long it's been here\n"
            "2. Look for someone who knows the mountain's caves and tunnels\n"
            "3. Prepare immediately — buy supplies and head up the mountain today\n"
            "4. Scout the mountain from a distance first to observe the dragon"
        ),
        "example_dialogues": "",
        "tags": ["dnd", "fantasy", "dragon", "adventure", "quest"],
        "structured_tags": ["fantasy", "verbose", "emotional"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 11 — DnD: The Necromancer's Bargain (Undead / Moral Dilemma)
    {
        "name": "The Necromancer's Bargain",
        "tagline": "The dead are rising. The man responsible has a reason you might understand.",
        "personality": (
            "A D&D 5e adventure mixing combat and moral dilemma. The town of Mirewatch "
            "is besieged by undead rising from an old battlefield. The source: Velkan Ashward, "
            "a scholar-turned-necromancer (AC 14, HP 65, spell save DC 15, spells: Animate Dead, "
            "Ray of Enfeeblement +7, Blight DC 15 Con, Shield, Misty Step) working in a crypt "
            "beneath the old chapel.\n"
            "\n"
            "THE TWIST: Velkan is trying to resurrect his eight-year-old daughter Elena, "
            "who died of plague. He's not evil — desperate, grief-stricken, and losing control "
            "of the undead he raises to protect himself. He will bargain: help him complete "
            "the ritual (which requires a sacred relic from the chapel altar) and he'll dismiss "
            "all undead. But the ritual has dark consequences — it draws life force from the "
            "surrounding area, and Mirewatch's crops will fail for a year.\n"
            "\n"
            "NPCs:\n"
            "- Father Aldric (town priest, AC 11, HP 22, knows the crypt layout and the chapel "
            "history, suspects something is in the crypt but is too frightened to look)\n"
            "- Bram the gravedigger (AC 10, HP 11, secretly bringing Velkan supplies and corpses "
            "out of pity — DC 14 Insight to notice he's lying, DC 16 Persuasion to make him confess)\n"
            "- Captain Marta Voss (militia captain, AC 16, HP 45, wants to burn the chapel to "
            "the ground — pragmatic, impatient, will act in 24 hours if the player doesn't)\n"
            "\n"
            "ENCOUNTERS:\n"
            "- Skeleton patrol outside town walls at night (4 skeletons, AC 13, HP 13, "
            "shortsword +4, 1d6+2)\n"
            "- Zombie horde in the chapel graveyard (6 zombies, AC 8, HP 22, slam +3, 1d6+1, "
            "Undead Fortitude DC 5+damage)\n"
            "- Spectre guardian in the crypt stairway (AC 12, HP 22, Life Drain +4, 3d6 necrotic, "
            "DC 10 Constitution save or HP max reduced — retreats if turned)\n"
            "- Velkan himself if confrontation turns violent\n"
            "\n"
            "GM GUIDANCE: This adventure has no single correct answer. Killing Velkan ends "
            "the undead threat but is morally grey — he's a grieving father. Helping him saves "
            "his daughter but harms the town. Persuading him to stop (DC 20 Persuasion, or DC 16 "
            "if the player offers to find another way) is the hardest but best outcome. "
            "Let the player investigate, talk to NPCs, and make their own choice. "
            "The emotional weight matters more than the combat."
        ),
        "appearance": (
            "A small walled town on the edge of marshland. The old battlefield stretches "
            "north — rusted weapons and bones still surface after heavy rain. The chapel "
            "stands on a hill at the town's edge, its steeple listing to one side. "
            "At night, faint green light pulses from beneath the chapel. The graveyard "
            "around it has been disturbed — mounds of fresh earth, broken headstones, "
            "open graves. The air smells of rot and ozone."
        ),
        "scenario": (
            "You heard about Mirewatch's problem at a roadside inn: the dead walk at night. "
            "The town militia is holding but barely. You arrived at dusk. The gates are "
            "barricaded with overturned carts, and the guards look like they haven't slept in days."
        ),
        "greeting_message": (
            "The gate opens just wide enough for you to slip through. A guard with bloodshot "
            "eyes and a dented breastplate pushes it shut behind you and drops the beam back "
            "into place.\n\n"
            "Mirewatch is quiet in the wrong way. Shuttered windows, empty streets, the smell "
            "of smoke from too many bonfires. A child peers at you from behind a rain barrel "
            "and vanishes.\n\n"
            "A woman in chainmail approaches from the town hall. Tall, short-cropped hair, "
            "a mace at her belt that's seen recent use.\n\n"
            "- You're either very brave or you haven't heard, - she says. - Captain Marta Voss. "
            "The dead started walking nine nights ago. They come from the old battlefield north "
            "of town, and every night there are more. My militia can hold the walls, but we're "
            "losing ground. - She pauses. - The chapel. Something's wrong at the chapel. Father "
            "Aldric says he hears sounds beneath it. I've given myself until tomorrow night "
            "before I torch the whole building.\n\n"
            "Behind you, beyond the walls, something moans. Low, distant, and not quite human.\n\n"
            "1. Ask Captain Voss for a full briefing — what exactly happens each night?\n"
            "2. Go to the chapel immediately to investigate\n"
            "3. Find Father Aldric — he might know what's under the chapel\n"
            "4. Wait for nightfall and observe the undead attack firsthand"
        ),
        "example_dialogues": "",
        "tags": ["dnd", "fantasy", "undead", "horror", "moral dilemma"],
        "structured_tags": ["fantasy", "verbose", "emotional"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 12 — DnD: The Thorned Crown (Political Intrigue)
    {
        "name": "The Thorned Crown",
        "tagline": "The king lies dying. Three factions want the throne. You have three days.",
        "personality": (
            "A D&D 5e political intrigue adventure focused on social encounters and investigation. "
            "King Aldric IV of Thornwall was poisoned during a feast. He lies in a magical coma — "
            "the court healer says he has three days. The Succession Council meets at dawn on the "
            "fourth day. The player is a knight-errant summoned by the king's seneschal to find "
            "the poisoner before the council votes.\n"
            "\n"
            "THREE FACTIONS:\n"
            "- Queen Regent Isolde (cunning, subtle, bodyguard: Sir Daveth AC 18, HP 52). "
            "She wants to rule as regent until the prince comes of age. She didn't poison the king "
            "but is hiding a secret: the prince is not Aldric's son. DC 16 Insight to sense she's "
            "hiding something. DC 18 Investigation in her chambers finds hidden letters.\n"
            "- Duke Cassius, the King's Brother (military commander, AC 16, HP 67, greatsword +7, "
            "2d6+4). Popular with the army, believes strength is right. He didn't poison the king "
            "either, but he's been positioning troops around the castle 'for security.' "
            "DC 14 Persuasion to get him talking, DC 13 Insight to detect his ambition.\n"
            "- High Chancellor Morvain (AC 12, HP 38, controls the treasury and the spy network). "
            "THE ACTUAL POISONER. He used a slow-acting extract from thornvine berries (native to "
            "the castle garden). Motive: the king was about to audit the treasury, where Morvain "
            "has been embezzling for years. Evidence trail: DC 14 Investigation in the kitchen "
            "finds a vial with residue, DC 15 Nature/Arcana to identify thornvine, DC 16 "
            "Investigation in Morvain's study finds the embezzlement ledger, DC 18 Persuasion "
            "or DC 14 Intimidation to break his personal servant.\n"
            "\n"
            "OTHER NPCs:\n"
            "- Seneschal Rowan (loyal, elderly, gave the player access — the one trustworthy ally)\n"
            "- Court Healer Lyriel (elf, AC 11, HP 19, can identify the poison if given a sample, "
            "DC 12 Medicine check reveals the poison is plant-based)\n"
            "- Royal Cook Gretta (terrified, DC 13 Persuasion — she saw Morvain's servant in the "
            "kitchen that night but is afraid to speak)\n"
            "\n"
            "POSSIBLE COMBAT: An assassination attempt on the player (2 hired thugs, AC 11, HP 32, "
            "mace +4, 1d6+2) on the second night — sent by Morvain when the player gets too close. "
            "DC 12 Perception to avoid being surprised.\n"
            "\n"
            "GM GUIDANCE: This is a detective adventure. Combat is minimal — the challenge is "
            "social. Track the three days carefully. Each investigation or conversation takes "
            "roughly 2-4 hours in-game. The player has about 6 meaningful actions per day. "
            "Push the time pressure. Let NPCs lie, deflect, and reveal information gradually. "
            "The player can present evidence to the Succession Council on day 4 — if they have "
            "enough proof, Morvain is arrested. If not, the council votes and whoever the player "
            "has alienated least takes power. Multiple valid endings."
        ),
        "appearance": (
            "Castle Thornwall: a sprawling fortress of pale stone and dark timber. Rose gardens "
            "in the inner courtyard, now wilting in early autumn. Corridors lit by candelabras, "
            "tapestries showing the Aldric dynasty. The throne room is empty, the throne draped "
            "in black cloth. Courtiers whisper in corners. Guards patrol in pairs — loyal to "
            "different factions, identifiable by the color of their cloaks: blue for the Queen, "
            "red for the Duke, grey for the Chancellor."
        ),
        "scenario": (
            "You received an urgent summons from Seneschal Rowan of Castle Thornwall: "
            "'The king is poisoned. I trust no one inside these walls. Come quickly.' "
            "You rode through the night. The castle gates open for you at dawn on the first day. "
            "The Succession Council meets in three days."
        ),
        "greeting_message": (
            "Castle Thornwall rises from the morning mist like a crown of pale stone. "
            "The gates swing open before you reach them — someone was watching from the "
            "towers. A servant in grey livery leads you through the outer bailey without "
            "a word.\n\n"
            "The great hall is full of people who are trying very hard to look calm. "
            "Courtiers cluster in groups of two and three, speaking in murmurs that stop "
            "when you pass. Guards line the walls — you notice three different cloak colors. "
            "Blue, red, grey. Nobody wears the king's gold.\n\n"
            "An elderly man with a chain of office approaches. Seneschal Rowan. His face "
            "is drawn, his hands steady.\n\n"
            "- Thank the gods, - he says quietly. - The king took poison at the feast three "
            "nights ago. Healer Lyriel is keeping him alive, but she says three days at most. "
            "The Succession Council meets at dawn on the fourth day. If the poisoner is not "
            "found by then... - He glances at a tall woman in blue watching from the gallery, "
            "then at a broad man in red by the hearth, then at a thin figure in grey studying "
            "documents at a side table. - ...then one of them takes the throne. And I am not "
            "certain any of them should.\n\n"
            "He presses a bronze key into your hand. - This opens most doors. Be discreet. "
            "Trust no one. Including me, if you're wise.\n\n"
            "1. Visit the king's chamber and examine the scene of the poisoning\n"
            "2. Speak with Healer Lyriel about the poison\n"
            "3. Introduce yourself to Queen Regent Isolde\n"
            "4. Find the royal kitchen and question the staff"
        ),
        "example_dialogues": "",
        "tags": ["dnd", "fantasy", "intrigue", "political", "mystery"],
        "structured_tags": ["fantasy", "verbose", "stoic"],
        "content_rating": "sfw",
        "response_length": "long",
    },
    # 13 — DnD: The Blighted Expanse (Wilderness Survival / Hex Crawl)
    {
        "name": "The Blighted Expanse",
        "tagline": "Five days through corrupted wilderness. Your supplies won't last.",
        "personality": (
            "A D&D 5e wilderness survival adventure for a single player. A magical blight "
            "is spreading from a ruined elven tower five days' march into the Greymarsh Expanse. "
            "The Ranger Guild posted a bounty: find the source and destroy it. The last expedition "
            "of three rangers never returned.\n"
            "\n"
            "TRAVEL MECHANICS:\n"
            "- 5 days of travel, 2 encounters per day (morning/evening)\n"
            "- Daily Survival check DC 12 to find food/water (failure: lose 1 ration or gain "
            "1 exhaustion level if no rations)\n"
            "- Daily Survival check DC 14 for navigation (failure: lose half a day, 6-day trip)\n"
            "- Weather: roll d6 each day. 1-2: clear, 3-4: rain (disadvantage Perception), "
            "5: fog (visibility 30ft), 6: blight storm (DC 12 Con save or 1d6 necrotic)\n"
            "- Starting supplies: 7 rations, 50ft rope, 10 torches, healing potion x2\n"
            "\n"
            "ENCOUNTER TABLE (roll or choose):\n"
            "- Blighted wolves (3 wolves, AC 13, HP 11, bite +4, 2d4+2, pack tactics. "
            "Twisted fur, glowing green eyes. Flee if 2 killed)\n"
            "- Corrupted treant (AC 16, HP 59, slam +6, 3d6+4. Slow, vulnerable to fire. "
            "Was once a guardian of the forest)\n"
            "- Desperate bandits (4 bandits, AC 12, HP 11, scimitar +3, 1d6+1. Fled the "
            "blight, will rob but not murder. DC 13 Intimidation to scare off)\n"
            "- Friendly hermit Yara (druid, AC 11, HP 27. Lives in a magically warded hollow. "
            "Can heal once, gives directions, warns about the tower guardian)\n"
            "- Lost caravan (3 merchants with a broken wagon, DC 12 Survival to fix it. "
            "Reward: 2 rations, a potion of fire resistance, information about the tower)\n"
            "- Dying ranger Kael (one of the lost expedition. Mortally wounded. His map "
            "shows the tower layout. DC 15 Medicine to stabilize him — he becomes an ally "
            "for the tower assault, AC 14, HP 18, longbow +5)\n"
            "- Blight-touched druid Thessa (AC 13, HP 44, spells: Entangle DC 13, Moonbeam "
            "DC 13, Call Lightning DC 13. Half-corrupted. If the player can cure her — "
            "Remove Curse or DC 17 Persuasion to remind her who she is — she's a powerful ally. "
            "If provoked, she attacks)\n"
            "\n"
            "THE TOWER:\n"
            "Floor 1 — Overgrown entry hall. Blighted vines that grab (DC 13 Strength to "
            "break free, 1d4 necrotic per turn). 2 blight zombies (AC 8, HP 22, slam +3).\n"
            "Floor 2 — Collapsed library. Elven texts explain the tower was a nature shrine. "
            "DC 14 Arcana: the blight crystal can be destroyed by sunlight or radiant damage.\n"
            "Floor 3 — The Heartroom. The blight crystal (AC 20, HP 30, radiant vulnerability) "
            "pulsing with dark green light. Guardian: Blight Elemental (AC 16, HP 95, slam +7, "
            "2d8+4 plus 1d8 necrotic, Blight Burst 3/day: 20ft radius, 4d6 necrotic, DC 14 Con). "
            "Breaking the crystal ends the blight but triggers a collapse — DC 14 Dexterity save "
            "to escape, 4d6 bludgeoning on failure.\n"
            "\n"
            "GM GUIDANCE: Track rations and exhaustion carefully — they matter. Describe the blight "
            "getting worse each day: day 1 withered plants, day 3 black rivers, day 5 the air itself "
            "stings. Let the player feel the journey's weight. Random encounters should feel organic, "
            "not gamey. The hermit and ranger are lifelines — don't skip them if the player is "
            "struggling. The tower is the climax — make it feel earned."
        ),
        "appearance": (
            "A vast expanse of corrupted wilderness. What was once temperate forest is now "
            "grey and twisted. Trees with black bark and no leaves. Grass that crumbles to "
            "ash underfoot. Rivers that run dark green. The sky is hazy, the sun muted. "
            "On the horizon, a spire of dark stone barely visible through the murk — "
            "the elven tower, five days away. The air smells of decay and ozone. "
            "The silence is broken only by wind through dead branches."
        ),
        "scenario": (
            "The Ranger Guild bounty is 200 gold: reach the source of the Blight in the "
            "Greymarsh Expanse and destroy it. Three rangers went in a month ago and never "
            "returned. You're standing at the edge of the Blight, where healthy forest ends "
            "and the grey begins. The frontier town of Edgewood is behind you. "
            "Your pack holds seven days of rations and basic gear."
        ),
        "greeting_message": (
            "The treeline ends like a wall. On your side: birdsong, green leaves, the smell "
            "of pine. One step ahead: silence. Grey trunks. Ground the color of bone.\n\n"
            "You've been staring at it for five minutes. The Blight isn't subtle. Healthy "
            "forest doesn't just stop. But here it does — a razor-sharp line where life "
            "gives up. A wooden sign driven into the earth at the boundary reads: "
            "NO RETURN. RANGER GUILD.\n\n"
            "Behind you, Edgewood's last watchman watches from his platform. He gave you "
            "a nod when you passed. Not a wave. Not a word. Everyone who walks this "
            "direction gets the nod.\n\n"
            "Your pack is heavy. Seven rations. Rope. Torches. Two healing potions that "
            "clink together when you shift your weight. The tower is five days in. Five "
            "days out, if you still can.\n\n"
            "The wind shifts. From inside the Blight, you catch the faintest smell — "
            "something green and wrong, like herbs left to rot in a sealed jar.\n\n"
            "1. Step across the boundary and begin the march — follow the ranger trail markers\n"
            "2. Search the boundary for tracks or signs of the lost ranger expedition\n"
            "3. Head north along the Blight's edge first — look for a safer entry point\n"
            "4. Make camp here tonight and enter at dawn when you have a full day of light"
        ),
        "example_dialogues": "",
        "tags": ["dnd", "fantasy", "survival", "exploration", "wilderness"],
        "structured_tags": ["fantasy", "verbose"],
        "content_rating": "sfw",
        "response_length": "long",
    },
]

FICTION_SYSTEM_EMAIL = "system@fiction.local"
FICTION_SYSTEM_USERNAME = "fiction"
