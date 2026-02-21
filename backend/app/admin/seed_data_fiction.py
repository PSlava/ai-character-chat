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
]

FICTION_SYSTEM_EMAIL = "system@fiction.local"
FICTION_SYSTEM_USERNAME = "fiction"
