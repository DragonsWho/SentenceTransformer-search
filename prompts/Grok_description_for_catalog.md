Create a compelling game description for our online catalog. The description must:
- Be 5-7 sentences maximum
- Have a strong, captivating first sentence that will serve as the preview on game cards
- Effectively convey the game's core concept, unique selling points, and emotional atmosphere
- Use vivid natural language and avoid generic marketing terms

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

If the game has specific themes, aesthetics, mechanics, or content not covered by standard tags, please add appropriate custom tags to highlight these features. Do not create new tags to describe unique items, characters, or areas. Be sure to create a tag if the game represents some popular fandom and it is a major part of the story, i.e. the game is a fanfic.

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