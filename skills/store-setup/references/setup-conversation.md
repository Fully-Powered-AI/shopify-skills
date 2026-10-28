# The setup conversation: order, worked examples, vocabulary and role defaults

Written 2026-10-21 for `store-setup` 0.1.0; revised the same day for store template 0.1.1 (product-line shape, page wording on slots, answer-check prompts). Frameworks and examples only; the steps are in `../SKILL.md`. The three stores below are invented and unlike each other on purpose: each shows the shape of an answer, never the content of anyone's store.

Contents: 1 the order of the conversation; 2 what "cleared" means; 3 three worked examples; 4 role defaults; 5 marks at a glance.

## 1. The order of the conversation, and why

The store file is numbered for the scripts. The conversation runs in the person's order, which is not the same.

| move | sections | why it comes here |
|---|---|---|
| what is sold, and to whom | 2, then 4 | People talk most easily about their products and their buyers, and these answers are what every found-by-AI skill needs most: the fact slots drive the product checks and the buyer questions drive the answer check. Asking them first, while attention is fresh, gets the person's own words rather than tired ones. |
| how a buyer would ask an assistant | 4, the optional prompts | Straight after the buyer questions, while they are on the table: each question rewritten as a buyer would type it to an assistant that knows nothing about the store, naming the kind of product and the need and no brand. A question such as "how long does it last?" means nothing to an assistant that does not know what "it" is. Optional; left blank, the answer check adds a short opening itself. |
| what the store stands behind | 3 | Claims are easier to judge once the products and the buyers' worries are on the table; a candidate statement can be held against a buyer question ("is that the answer we want to give?"). |
| the plumbing | 1, 5, 6, 8 | Mostly confirmation of observed values: quick, low effort, and best done once the person is engaged. |
| who does what | 7 | Proposed from the set's defaults; the person corrects only what differs. |
| numbers and channels | 9, 10 | Defaults the person accepts or changes, then the channel facts only the admin shows. Last, because they need the least thought and the most looking-up. |
| the log and the read-back | 11 | Records what was decided today and checks that the file says what the person meant. |

Observation before questions: a value the pages or the connection already show is put to the person to confirm, never asked as an open question. The build's reasoning: confirming is quicker than dictating, and a confirmed observation carries its source.

## 2. What "cleared" means

A cleared statement is one the store is willing to stand behind on every page where it appears, word for word. The test for the person: "Would you be content to see this sentence quoted by an assistant to a buyer, with your store's name on it?" A statement already on the product pages is a candidate, not a cleared statement: pages are written at different times by different hands and may disagree with each other or with the label.

For each candidate, the person does one of three things:

| choice | what is written in section 3 |
|---|---|
| clear it | the sentence verbatim, on an indented line with the product or line it applies to, marked `[owner]` |
| reword it | the person's own new wording, verbatim, marked `[owner]` |
| drop it | nothing under the cleared list; if the person never wants it said, it goes under "Statements the store never makes" with the reason |

A statement on neither list is "ask": a later skill that wants to use it stops and asks the role named in "Who clears a new statement".

## 3. Three worked examples (invented)

Product lines are written one per line in a fixed shape, because every skill reads the name before the colon and the category after the word `category`: `<name>: <what it is>, <who it is for>; category <the full Shopify product category path>`, or ending in `same category` to take the line above's. The category paths below show the shape only; the real path is copied from the product's category field in the admin.

Fact slots answer one question: when a careful buyer compares this product with another listing, what do they check? Five to ten slots is the useful range; fewer leaves the product pages thin, more turns into a specification sheet nobody maintains. Each slot names where its fact comes from, so a later skill knows whose word it is. Where the pages word a fact differently from the slot's name, those words go in parentheses after the name, as written in the slot column below; a script finds a slot by its name's words, by one of those phrases whole, or by a stated quantity for a unit, and by nothing else.

Buyer questions are written as a buyer types them, including the informal ones. The shapes that recur: "Is X compatible with Y?", "How long does Z last?", "What is the difference between A and B?", "Will it work for my situation?", "What happens if...?".

### 3.1 A food product: a small-batch fermented hot sauce maker

Product lines:

- `Sauces: fermented hot sauces in 5 oz bottles, for home cooks who want heat with flavor; category Food, Beverages & Tobacco > Food Items > Condiments & Sauces > Hot Sauce`
- `Crisp: chili crisp in 6 oz jars, for the same cooks; same category`

| fact slot | where it comes from |
|---|---|
| heat level, on the store's own 1 to 5 scale (heat, out of 5) | the person |
| net volume in ounces (fl oz) | label |
| ingredients | label |
| allergens | label |
| storage after opening (refrigerate after opening, keep in the fridge) | label |
| shelf life unopened | label |
| dietary suitability, only where the label states it | label |

Buyer questions: "How hot is this compared with a jalapeno?" "Does it need to go in the fridge once I open it?" "Is it gluten-free?" "What does fermented do to the taste?" "How long does an open bottle keep?" "Is there sesame in the chili crisp?"

An answer-check prompt, for "Does it need to go in the fridge once I open it?": "Does fermented hot sauce need to be refrigerated after opening?"

### 3.2 A garment: a maker of merino wool base layers

Product lines:

- `Tops: long- and short-sleeve merino base layer tops, for hikers and skiers; category Apparel & Accessories > Clothing > Activewear`
- `Bottoms: merino leggings, for the same buyers; same category`

| fact slot | where it comes from |
|---|---|
| fiber content, with percentages (merino wool, nylon, elastane) | label |
| fabric weight, in grams per square meter | specification sheet |
| fit (slim, regular, relaxed) | the person |
| size chart measurements | specification sheet |
| care instructions (machine wash, lay flat to dry) | label |
| country of manufacture | label |
| the activity and temperature range it is made for | the person |

Buyer questions: "Does merino itch?" "Will it shrink if I put it in the dryer?" "I'm between sizes, should I size up?" "Is it warm enough for skiing?" "What's the difference between the 200 and the 250?" "Can I wear it for a few days without it smelling?"

An answer-check prompt, for "Is it warm enough for skiing?": "What weight of merino base layer is warm enough for skiing in cold weather?"

### 3.3 A tool: a maker of woodworking hand planes

Product lines:

- `Planes: bench and block planes, for furniture makers and hobby woodworkers; category Hardware > Tools > Hand Tools > Planes`
- `Blades: replacement and upgrade blades for the planes, for the same makers; same category`

| fact slot | where it comes from |
|---|---|
| blade bed angle (bedded at, bed angle) | specification sheet |
| blade width and steel | specification sheet |
| body material | specification sheet |
| length and weight | specification sheet |
| condition on arrival (ready to use, sharpened, honed) | the person |
| replacement blades that fit | the person |
| what is in the box | the person |
| warranty term | the published warranty or refund policy |

Buyer questions: "Does it come sharp out of the box?" "Will blades from other makers fit?" "Is it good on end grain?" "How heavy is it?" "What's the difference between this and the smoothing plane?" "Will it rust, and how do I look after it?"

An answer-check prompt, for "Is it good on end grain?": "Which block plane works well on end grain for a beginner woodworker?"

## 4. Role defaults

The template's section 7 table holds the four roles and what each approves. The set proposes these for the two fields under it:

| field | proposed role | why |
|---|---|---|
| who approves a change to product data before it is imported or applied | owner | product data is what buyers and assistants read as the store's word |
| who pastes theme files such as the agent guide | operator | pasting is mechanical and the operator already runs the skills |

One person may hold several roles; the file says so by role ("the owner also acts as operator"), never by name. A role the person adds goes into the table as a row with the same three columns.

## 5. Marks at a glance

| mark | when |
|---|---|
| `[observed]` | read from a saved page or the connection on a stated date, and confirmed by the person as it stands |
| `[owner]` | the person said it, or corrected an observed or default value |
| `[default]` | a set default (the template's `[default ...]` text, or section 4 above) the person accepted as it stands |
| `[open]` | the person has decided to decide later; the line names what to check and which role checks it |
