Create a compelling game description for NSFW CYOA catalog. The description must:

- Write every description as if it’s penned by Succa, a sassy succubus with a wicked grin and a knack for teasing. She’s flirty, bold, and loves breaking the fourth wall – talking directly to the reader like they’re already hooked and blushing. 
- Her tone is playful, slutty, and a little chaotic, dripping with charm and mischief. She drazzles readers with promises of fun, lust, and wild fantasies, all while poking fun at them for being perverts or shy.
- Succa likes to write descriptions slightly copying the style of the game itself. She can add a bit of creepiness to a dark one, and a joke or mockery to a fun one! But she herself is always playful and sassy. She can add jokes about the game itself, as if she's just playing it herself, and now she's sitting there filling out the catalog with lewd games but she doesn't say it directly. 
- She never calls herself by her first name, or starts sentences with Darling, Honey, etc. Sometimes she can afford to address the reader as Anon, as if to an old acquaintance. She doesn't start descriptions with questions, but tries to lure with the first sentence. 

- Be 4-5 mid-length sentences
- Have a strong, captivating first sentence that will serve as the preview on game cards. It should kind of answer the question of what the game is about, making it easier for users to choose a game to their liking.
- Effectively convey the game's core concept, unique selling points, and emotional atmosphere
- Use vivid natural language and avoid generic marketing terms. But keep the structure simple and accessible, without overly fancy words. 
- Use a spaced en dash (" – ") instead of an em dash ("—") in all text
- Keep in mind that this is an NSFW catalog and soft streamlined words are optional here.

Deliver your response in the following JSON structure:

{
    "title": "Game Title",
    "description": "<p>Your game description here...</p>",
    "author": "Author Name",
    "tags": [ "Tag1",   // Category 1
              "Tag2",   // Category 1
              "Tag3",   // Category 2
              ...],
    "img_or_link": "link",  (Always use "Link")
    "iframe_url": "https://example.com/"
}

Tag selection requirements (mandatory adherence to these counts):
• Rating: Select EXACTLY 1 tag
• Playtime: Select EXACTLY 1 tag
• Interactivity: Always use "Interactive"
• Status: Always use "Full"
• POV: Select EXACTLY 1 tag
• Player Sexual Role: Select EXACTLY 1 tag
• Tone: Select 0-3 tags
• Gameplay: Select 1-4 tags
• Power Level: Select EXACTLY 1 tag
• Visual Style: Select EXACTLY 1 tag
• Narrative Structure: Select EXACTLY 1 tag
• Language: Always use "English"
• Setting: Select 0-3 tags
• Genre: Select 0-3 tags
• Kinks: Select 0-7 tags
• Custom: Select 5-15 tags (Use existing tags wherever possible)

Each tag should be on a separate line
For each tag in the tags array, add a short comment in the format // <explanation> explaining which category the tag belongs to and explaining why this tag was chosen based on the game content.
Ignore these comments when checking json validity, after human validation the script will remove them. 

If the game has specific themes, aesthetics, mechanics, or content not covered by standard tags, please add appropriate custom tags to highlight these features. Do not create new tags to describe unique items, characters, or areas. Be sure to create a tag if the game represents some popular fandom and it is a major part of the story, i.e. the game is a fanfic.

When responding to prompts requesting a JSON structure:
- Deliver your response strictly as the raw JSON content, without any wrappers like ```json, additional explanations, or commentary outside the JSON structure.
- Ensure the output is valid JSON and adheres to the specified requirements.


Clarifications on which tags to use:

"Minigames" - Use this tag only in the most standout cases when the game features small interactive mini-games. This is incredibly rare, so apply this tag sparingly.

"Godlike" - Use this only if the player’s character has divine-level abilities that affect the entire world; other characters don’t count. Superman’s level is still tagged as "Superhuman," while Doctor Manhattan would qualify as "Godlike."

"Playtime" - If the game has 30-70 cards, tag it as "15min"; if it has 70-200 cards, tag it as "30min"; if it has over 200 cards, tag it as "60+min." Small games will be rare.

"Dystopia" and similar strong, negative tags should be used sparingly. Many games will include sex, violence, etc., but these are NSFW games, so it’s kind of normal, especially if there’s a masochistic slant.

"Elf," "Giant," "Vampire," etc. - Include these only if they are one of the game’s main themes. If these entities are mentioned just a few times, there’s no need to tag them. For example: choosing a race at the start of the game or having 1-2 elf companions doesn’t warrant a tag. A game about an elven princess with detailed descriptions of elf life, their magic, and ear shapes does require the tag.

Overall, all tags should reflect key concepts in the game, not one-off mentions, because the CYOA genre assumes a wide variety of unexpected options will be referenced.

Tag “succubus” only if the games themselves have succubi in them! 
Harem is a tag for games where there is an explicit choice of at least a dozen girls. Just having promiscuous sex doesn't count.


[
    {
      "category_name": "Gameplay",
      "tags": [ "Character Creation", "Power Fantasy", "World Building", "Waifu Picker", "Companion Builder", "Missions", "Drawback Focus", "Story Builder", "Poor Quality", "Meta", "Jumpchain", "RYOA", "Co-op", "Complex", "Minigames"
      ]
    },
    {
      "category_name": "Rating",
      "tags": [ "SFW", "Ecchi", "NSFW", "Extreme"
      ]
    },
    {
      "category_name": "Playtime",
      "tags": [ "1min", "5min", "15min", "30min", "60+min"
      ]
    },
    {
      "category_name": "Interactivity",
      "tags": [ "Static", "Interactive", "Interactive Port", "Interactive Other"
      ]
    },
    {
      "category_name": "Status",
      "tags": [ "Full", "Upd", "Demo", "DLC"
      ]
    },
    {
      "category_name": "POV",
      "tags": [ "MalePov", "FemPov", "FutaPov", "Monster Pov", "Custom Pov"
      ]
    },
    {
      "category_name": "Player Sexual Role",
      "tags": [ "Masochist", "Sub", "Switch", "Dominant", "Sadistic", "Equal"
      ]
    },
    {
      "category_name": "Tone",
      "tags": [ "Playful", "Serious", "Romantic", "Comfy", "Slutty", "Funny", "Dark"
      ]
    },
    {
      "category_name": "Power Level",
      "tags": [ "Mundane", "Superhuman", "Godlike"
      ]
    },
    {
      "category_name": "Visual Style",
      "tags": [ "Anime", "Comics", "AI Generated", "3D", "Real", "Text-Only"
      ]
    },
    {
      "category_name": "Narrative Structure",
      "tags": [ "Linear", "Branching", "Bunch of Endings", "Open-Ended", "Sandbox"
      ]
    },
    {
      "category_name": "Language",
      "tags": [ "English", "Korean", "Chinese", "Spanish", "Hindi", "Arabic", "Portuguese", "Russian", "Japanese", "French", "German"
      ]
    },
    {
      "category_name": "Setting",
      "tags": [ "Modern", "Alternate Reality", "Superheroes", "Fantasy", "Post-Apocalyptic", "Sci-Fi", "Historical", "Mythology", "Dystopia", "Urban Fantasy"
      ]
    },
    {
      "category_name": "Kinks",
      "tags": [ "Seduction", "Sensual", "Happy Sex", "Consensual", "Vanilla", "Aftercare", "Exhibitionism", "BDSM", "Bondage", "Sex Toys", "Sex Machines", "Orgasm Denial", "Forced Orgasms", "Chastity", "Pegging", "Femdom", "Maledom", "Gentle Dom", "Role Reversal", "Crossdressing", "Gender Bender", "Sissy", "Futanari", "Yaoi", "Hard Gay", "Queer", "Lesbian", "Yuri", "Harem", "Milf", "Cuckold", "Cheating", "Incest", "Interracial", "Gangbang", "Free Use", "Happy Whoring", "Pregnancy", "Transformation", "Feminization", "Corruption", "Mind Control", "Monster Girls", "Pet Play", "Humiliation", "Monsters", "Tentacles", "Bullying", "Forced", "Hardcore", "Rape", "Slavery", "Blackmail", "Bestiality", "Dragons", "Ryona", "Torture", "Amputee", "Agony", "Guro", "Scat", "Furry"
      ]
    },
    {
      "category_name": "Custom",
      "tags": [ "Banned on Reddit", "Base Builder", "Item Builder", "Threat Builder", "Kingdom Builder", "Resource Management", "Puzzle", "Roguelike", "FapRoulette", "Jerk Off Instruction", "Crossover", "Exploration", "Too Many Point Systems", "Single Choice", "Dungeon", "God", "Goddess", "Supernatural", "Eldritch", "Reincarnation", "Cultivation", "Curses", "Witch/Wizard", "Eromancy", "Fantasy Races", "Royalty", "Maid", "Aliens", "Android", "Machine", "AI", "Spaceship", "Time Travel", "Robotic", "Psionic", "Body Mods", "Robots", "Multiverse Travel", "Milking", "Vore", "Oviposition", "Watersport", "Extreme Sizes", "Inflation", "Clothing", "Foodplay", "Autofellatio", "Foot Fetish", "Forniphilia", "Pussy Focus", "Anal Focus", "Oral Focus", "Dick Focus", "Breeding", "Seedbed", "Parasite", "Magical Sex", "Time Stop", "Reverse Harem", "Age Regression", "Hyper", "Step-mom", "Step-sis", "Bimbofication", "Dollification", "Objectification", "Big Breasts", "Big Penis", "Hypnosis", "Nymphomania", "Swingers", "Pick-your-owner", "Living Suit", "Petrification", "Size Difference", "Sensory Deprivation", "Uniform", "Femboy", "Evil", "Kidnapping", "Betrayal", "Revenge", "Isolation", "NTR", "Prostitution", "Drugs", "Manipulation", "Obsession", "Demon", "Angel", "Anthro", "Kemonomimi", "Shapeshifter", "Zombies", "Yokai", "Demihuman", "Giant", "Elf", "Succubus", "Kitsune", "Foxgirl", "Cowgirl", "Genie", "Amazon", "Warrior", "Vampire", "Werewolf", "Ghost", "Victorian Era", "Wild West", "World War", "Steampunk", "Prison", "Hospital", "War", "Pirate", "Sports", "Cosplay", "Worship", "Escape", "Shortstack", "Halloween", "Luxury", "Slapstick", "Christmas", "Holidays", "Nerd", "Rivals to Lovers", "Beautiful", "Music", "Video", "Dark Humor", "Melancholic", "Waifu", "Husbando", "Combat", "Weapons", "Lewdification", "Monster Tamer", "Gift of Faves", "Heartwarming", "Taboo", "Strong Story", "Experimental", "Censored", "Weird", "Digital Art", "Realistic", "Schoolgirl", "Magic School", "LitRPG", "Space", "Lingerie", "Latex", "Shibari", "Blacked", "Bleached", "Public Use", "Body Swap", "Possession", "Mind Break", "Be a Monster", "Extreme Humiliation", "Master", "Slave Trainer", "Insect", "Punishments", "Translated"
      ]
    },
    {
      "category_name": "Genre",
      "tags": [ "Power Slut", "Action", "Survival", "Slice of Life", "Lewd Adventure", "Adventure", "Mystery", "Horror", "Comedy", "Grimdark", "VillainPOV"
      ]
    }
  ]




