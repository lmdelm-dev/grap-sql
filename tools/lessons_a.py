"""Lessons L01-L10: from absolute zero to JOINs. Authored as data -> JSON."""

H = lambda a, b, c, d: [a, b, c, d]


def st(kind, title, prompt, **kw):
    """One exercise step. Accepts exp=, seed=, trick= as friendly aliases."""
    aliases = {"exp": "expected_sql", "seed": "seed_sql", "trick": "memory_trick"}
    for old, new in aliases.items():
        if old in kw:
            kw[new] = kw.pop(old)
    return {"type": kind, "title": title, "prompt": prompt, **kw}


def L01():
    return {
        "id": "L01", "order": 1, "difficulty": 1, "tags": ["intro", "database"],
        "title": "What is a database?",
        "steps": [
            st("answer", "A place full of tables",
               "Before we write anything, let's agree on the big idea.\n"
               "A DATABASE is a place where information lives, kept in an orderly way so a computer can find it fast.\n"
               "Real-life match: imagine a whole room of neatly labelled filing cabinets - each cabinet is a TABLE.",
               task="In SQL, one of these shapes is a table. Which one?",
               check={"answer": [
                   "a grid of rows and columns", "a sheet of rows and columns",
                   "rows and columns", "an excel sheet", "a grid",
                   "a table of rows and columns",
               ]},
               hints=H("Picture the filing cabinet in the example.",
                       "A table has a header across the top and items going down.",
                       "Excel sheets and spreadsheets are the closest everyday thing.",
                       "Answer: a grid of rows and columns."),
               trick="A table = one tidy grid."),
            st("build", "Meet the shop",
               "Great! Our practice data is a little MOROCCAN SHOP: spices, rugs, lanterns, argan oil.\n"
               "Everything in it - products, customers, sales - lives in its own table.\n"
               "Let's open the door. Run this (the 'Type it for me' button puts it in for you):",
               task="Run: SELECT * FROM products;",
               exp="SELECT * FROM products;",
               check={"demo": True},
               hints=H("Press the 'Type it for me' button next to the typing box.",
                       "Then press Run - or hold Ctrl and press Enter.",
                       "The star * in SQL means 'every column'.",
                       "The answer is just SELECT * FROM products;"),
               trick="SELECT = ask. The * means 'everything'."),
            st("answer", "Row vs column",
               "A database table is laid out in a grid.\n"
               "Going across, one line of the table is called a ROW - one product, with all its details.\n"
               "Going down, one heading like 'price' is called a COLUMN - one kind of fact for every product.",
               task="Each line across the table (one product) is called a…?",
               check={"answer": ["row", "a row", "record"]},
               hints=H("One item going across.", "One whole product with all its facts.",
                       "Lying down is a row. Standing up is a column.",
                       "Answer: a row."),
               trick="Row = lying down, Column = standing up."),
            st("answer", "Why learn SQL?",
               "Talking to the database is done with SQL (say it: 'ess-cue-ell').\n"
               "SQL is just short English words the database understands: SELECT, FROM, WHERE.\n"
               "A QUERY is one question you ask the database. Like asking a librarian for a book.",
               task="In SQL, what do we call one question you ask the database?",
               check={"answer": ["query", "a query", "an sql query", "a question"]},
               hints=H("You just asked one when you ran the shop.", "It starts with SELECT.",
                       "The librarian hears it as one sentence.", "Answer: a query."),
               trick="Query = one question to the database."),
        ],
    }


# --------------------------------------------------------------------------
def L02():
    return {
        "id": "L02", "order": 2, "difficulty": 1, "tags": ["select", "columns"],
        "title": "Your very first SELECT",
        "steps": [
            st("type", "Ask for one column",
               "SELECT means 'ask for'. To see all the product names, you write SELECT name.\n"
               "FROM products tells SQL which table to look in. In plain words: 'show me the names from the products table.'\n"
               "Type it with the ghost help (the grey text turns coral, then green as you get it right):",
               task="Try typing: SELECT name FROM products;",
               exp="SELECT name FROM products;",
               trick="SELECT … FROM … = ask the table for…",
               hints=H("Start with the word SELECT.", "The column we want is called name.",
                       "The table is called products and is named after FROM.",
                       "Write exactly: SELECT name FROM products;"),
            ),
            st("type", "Two columns at once",
               "One column was easy - let's ask for two. You list them after SELECT, separated by a comma.\n"
               "Writing SELECT name, price means: 'show me the names AND the prices.'",
               task="Try typing: SELECT name, price FROM products;",
               exp="SELECT name, price FROM products;",
               trick="A comma between columns = 'and also show me this'.",
               hints=H("Keep SELECT name and FROM products.", "Add a comma, then the second column.",
                       "The second column is called price.", "Write: SELECT name, price FROM products;"),
            ),
            st("type", "Only the price",
               "Say you only care about prices today. You don't have to take the whole table.\n"
               "You ask for exactly the column you want - that's the whole trick of SELECT.",
               task="Try typing: SELECT price FROM products;",
               exp="SELECT price FROM products;",
               trick="You get back only what you ask for.",
               hints=H("The column names live between SELECT and FROM.", "We want prices only.",
                       "It's a single word that starts with 'p'.", "Write: SELECT price FROM products;"),
            ),
            st("predict", "Predict the output",
               "Look at this query, and predict what you'll see: SELECT name FROM products;\n"
               "It's like asking the librarian for one list. Visualise it before you answer.",
               task="What will you see in the result?",
               check={"answer": ["all the product names", "the names of all products",
                                 "a list of names", "product names", "names of all products"]},
               hints=H("We asked for one column.", "Which one? The one that holds names.",
                       "Look at the word after SELECT.", "Answer: all the product names."),
               trick="The output is exactly the column you named.",
            ),
            st("answer", "There is a pattern",
               "Every query you write today has the same skeleton:\n"
               "SELECT the things you want, FROM the table they live in.\n"
               "Get used to that skeleton - every lesson from here builds on it.",
               task="Which word comes after FROM in the query SELECT name FROM products; ?",
               check={"answer": ["products", "products table", "the products table"]},
               hints=H("FROM points at the place to look.", "It's the name of the table.",
                       "It sells spices, rugs and lanterns.", "Answer: products."),
               trick="FROM = 'look inside this table'.",
            ),
        ],
    }


# --------------------------------------------------------------------------
def L03():
    return {
        "id": "L03", "order": 3, "difficulty": 1, "tags": ["select", "columns", "star"],
        "title": "Choosing exactly the columns you want",
        "steps": [
            st("fill", "Fill in the missing word",
               "Here's a query with one blank. Ask for the PRICE column:\n"
               "SELECT ___ FROM products;\n"
               "Replace the ___ with the column's name.",
               task="Fill the blank so the query shows prices.",
               seed="SELECT ___ FROM products;",
               exp="SELECT price FROM products;",
               hints=H("The blank sits right after SELECT.", "One word, starts with 'p'.",
                       "It's the prices of products.", "Replace ___ with price."),
               trick="Whatever you write after SELECT is what you see."),
            st("type", "Three columns",
               "More columns, same idea - just keep adding commas.\n"
               "This is called choosing a PROJECTION: you shine a light on only the columns you need.",
               task="Try typing: SELECT name, price, stock FROM products;",
               exp="SELECT name, price, stock FROM products;",
               trick="Three columns, two commas. Count them!",
               hints=H("Start from SELECT name, price …", "The third column is stock.",
                       "Add a comma before the last one.", "Write: SELECT name, price, stock FROM products;"),
            ),
            st("fix", "Fix the broken query",
               "Someone typed this and the database complained:\n"
               "SELECT name price FROM products;\n"
               "Can you spot the missing thing? SQL needs it to know where one column ends and the next begins.",
               task="Fix the query so it returns both name and price.",
               seed="SELECT name price FROM products;",
               exp="SELECT name, price FROM products;",
               hints=H("Read it aloud: 'SELECT name price' - that sounds joined together.",
                       "In a list, what marks the end of one item?",
                       "Name and price are two different columns of one list.",
                       "Add a comma between name and price."),
               trick="Columns in a list are joined by commas, like items on a shopping list."),
            st("type", "The star shortcut",
               "Sometimes you do want every column. The * (star) is SQL's shortcut: 'all of them.'\n"
               "SELECT * means 'every column.' It's the lazy-but-handy choice.",
               task="Try typing: SELECT * FROM products;",
               exp="SELECT * FROM products;",
               trick="* = the whole row, all columns.",
               hints=H("We want every column.", "There's a one-character shortcut.",
                       "It's the star symbol on your keyboard.", "Type: SELECT * FROM products;"),
            ),
            st("predict", "Predict the output",
               "What will SELECT * FROM customers; show you?\n"
               "(Look at the customers table before you answer.)",
               task="How many columns does the result have?",
               check={"answer": ["4", "four", "four columns", "4 columns"]},
               hints=H("Run the query in the Output pane to peek - prediction is fair game.",
                       "Count the headings the table has.",
                       "name, email, city, and one more.",
                       "Answer: 4 columns."),
               trick="* gives you exactly the same columns as the table."),
        ],
    }


# --------------------------------------------------------------------------
def L04():
    return {
        "id": "L04", "order": 4, "difficulty": 2, "tags": ["where", "filter"],
        "title": "WHERE: asking for only the rows you want",
        "steps": [
            st("type", "The big new word: WHERE",
               "SELECT picks the COLUMNS. WHERE picks the ROWS.\n"
               "WHERE is a filter - imagine a sieve. Only the rows that pass through the holes stay.\n"
               "WHERE price > 100 means: 'only rows whose price is above 100.'",
               task="Try typing: SELECT name FROM products WHERE price > 100;",
               exp="SELECT name FROM products WHERE price > 100;",
               trick="WHERE = 'only the rows that…'",
               hints=H("Start with SELECT name FROM products.", "Add WHERE after FROM products.",
                       "Write the condition: price > 100.", "Type: SELECT name FROM products WHERE price > 100;"),
            ),
            st("fill", "Fill in the comparison symbol",
               "SQL compares numbers with three little symbols:\n"
               " > means 'bigger than'    < means 'smaller than'    = means 'is exactly'\n"
               "The query below should list products that are OUT OF STOCK (0 left).\n"
               "One symbol is missing - it has been replaced by a blank ( ___ ).\n"
               "Change the ___ so the query means 'stock is exactly 0':\n"
               "SELECT name FROM products WHERE stock ___ 0;",
               task="Replace the ___ with a symbol so it says 'stock is exactly 0'.",
               seed="SELECT name FROM products WHERE stock ___ 0;",
               exp="SELECT name FROM products WHERE stock = 0;",
               hints=H("A blank ( ___) sits where a symbol should be. Delete it and type a symbol.",
                       "We want 'stock is exactly 0' - not bigger than 0 and not smaller than 0.",
                       "The symbol for 'is exactly' is one equals sign.",
                       "Final query: SELECT name FROM products WHERE stock = 0;"),
               trick="= means 'is exactly'. Write it once (not ==)."),
            st("type", "Text needs little wings",
               "Words in SQL are written inside single quotes, like little wings: 'Marrakech'.\n"
               "Numbers never need quotes - only text does.",
               task="Try typing: SELECT name, city FROM customers WHERE city = 'Marrakech';",
               exp="SELECT name, city FROM customers WHERE city = 'Marrakech';",
               trick="Text in quotes, numbers bare.",
               hints=H("Start with SELECT name, city FROM customers.",
                       "Add WHERE city = …", "Wrap Marrakech in single quotes.",
                       "Type: SELECT name, city FROM customers WHERE city = 'Marrakech';"),
            ),
            st("fix", "Fix the double equals",
               "A learner typed two equals signs - SQL only wants one:\n"
               "SELECT name FROM products WHERE stock == 0;\n"
               "Fix it.",
               task="Fix the query so it returns products with zero stock.",
               seed="SELECT name FROM products WHERE stock == 0;",
               exp="SELECT name FROM products WHERE stock = 0;",
               hints=H("Something is doubled.", "In SQL, one equals sign means 'is exactly'.",
                       "One = is enough. Two is a mistake here.",
                       "Change == to a single =."),
               trick="Exactly one equals sign in SQL."),
             st("predict", "Predict: how many?",
                "Predict a NUMBER before it runs:\n"
                "SELECT count(*) FROM products WHERE price > 100;\n"
                "count(*) returns a single number: how many rows pass the filter.",
                task="How many products cost more than 100 MAD?",
                check={"answer": ["21", "21 products", "twenty one"]},
                hints=H("This query filters with price > 100.", "count(*) counts the rows that pass.",
                        "Run it to check your guess - prediction lets you peek.",
                        "Answer: 21."),
                trick="Predicting numbers trains your database intuition."),
        ],
    }


# --------------------------------------------------------------------------
def L05():
    return {
        "id": "L05", "order": 5, "difficulty": 2, "tags": ["order by", "sort"],
        "title": "ORDER BY: putting rows in a tidy line",
        "steps": [
            st("type", "Sorting from small to big",
               "A database returns rows in the order it stored them - not very helpful.\n"
               "ORDER BY fixes that. It's like putting books on a shelf by height.",
               task="Try typing: SELECT name, price FROM products ORDER BY price;",
               exp="SELECT name, price FROM products ORDER BY price;",
               trick="ORDER BY = 'sort the rows by…'",
               hints=H("Start with SELECT name, price FROM products.",
                       "Add ORDER BY after FROM products.",
                       "We want to sort by price.",
                       "Type: SELECT name, price FROM products ORDER BY price;"),
            ),
            st("fill", "Smallest first or biggest first?",
               "ORDER BY price puts the SMALLEST first.\n"
               "Add DESC (from 'descending') to flip it to the BIGGEST first:\n"
               "SELECT name, price FROM products ORDER BY price ___;",
               task="Fill the blank so the most expensive product is first.",
               seed="SELECT name, price FROM products ORDER BY price ___;",
               exp="SELECT name, price FROM products ORDER BY price DESC;",
               hints=H("The blank comes right after price.",
                       "There's a magic word that makes it go down the ladder.",
                       "It starts with a D.", "Write DESC."),
               trick="DESC = descending = biggest on top."),
            st("type", "The most expensive three",
               "Combine your two new powers: ORDER BY and DESC.\n"
               "The output will read like a countdown of prices, top row = most expensive.",
               task="Try typing: SELECT name, price FROM products ORDER BY price DESC;",
               exp="SELECT name, price FROM products ORDER BY price DESC;",
               trick="DESC turns the list into a countdown.",
               hints=H("Start with SELECT name, price FROM products.",
                       "Add ORDER BY price, then DESC at the end.",
                       "The first row should now be the rug worth 3356.82 MAD.",
                       "Type: SELECT name, price FROM products ORDER BY price DESC;"),
            ),
            st("fix", "Fix the typo",
               "A sleepy learner mixed up the letters:\n"
               "SELECT name, stock FROM products ORDEY BY stock;\n"
               "The database pointed at the spelling. Fix it.",
               task="Fix the query so it sorts by stock.",
               seed="SELECT name, stock FROM products ORDEY BY stock;",
               exp="SELECT name, stock FROM products ORDER BY stock;",
               hints=H("Run it first and read the error.", "One word is misspelled.",
                       "ORDER BY has five letters in the first word.", "Change ORDEY to ORDER."),
               trick="Read errors like a friend: they are clues, not scoldings."),
            st("predict", "Predict the first row",
               "SELECT name, stock FROM products ORDER BY stock; \n"
               "starts from the smallest stock. Which product is at the TOP?",
               task="Which product name appears first?",
               check={"answer": [
                   "ras el hanout blend 100g", "ras el hanout", "ras el hanout blend",
                   "cumin ground 80g", "the ras el hanout blend 100g",
               ]},
               hints=H("There are several products with 0 stock.", "Run the query to see them.",
                       "The first one is decided by the order the table stores them in.",
                       "It starts with 'Ras el Hanout…'."),
               trick="When stocks tie, the tie order isn't promised - notes to self: ORDER BY stock, name is the tidy way."),
        ],
    }


# --------------------------------------------------------------------------
def L06():
    return {
        "id": "L06", "order": 6, "difficulty": 2, "tags": ["limit", "top n"],
        "title": "LIMIT: the database's 'just the first few'",
        "steps": [
            st("fill", "Top 3 heavyweights",
               "LIMIT chops the result after N rows - like asking the librarian to start at the top and only read the first three cards.\n"
               "Combine it with ORDER BY … DESC to get the three most expensive products:",
               task="Fill the blank: SELECT name, price FROM products ORDER BY price DESC LIMIT ___;",
               seed="SELECT name, price FROM products ORDER BY price DESC LIMIT ___;",
               exp="SELECT name, price FROM products ORDER BY price DESC LIMIT 3;",
               hints=H("We want the heavyweights - the priciest.", "The query already sorts DESC.",
                       "LIMIT is like saying 'stop after…'.", "Write 3."),
               trick="LIMIT cuts the list after N rows."),
            st("type", "Run it for real",
               "Now type the whole thing yourself, no blank this time.",
               task="Try typing: SELECT name, price FROM products ORDER BY price DESC LIMIT 3;",
               exp="SELECT name, price FROM products ORDER BY price DESC LIMIT 3;",
               trick="Bottom line of the query = how many rows you keep.",
               hints=H("Start with SELECT name, price FROM products.",
                       "Add ORDER BY price DESC.", "Finish with LIMIT and a number.",
                       "Write LIMIT 3 at the very end."),
            ),
            st("type", "A quick peek",
               "LIMIT is brilliant for a quick look at strange tables: 'just show me a sample.'\n"
               "You type * to get all columns, then LIMIT 5 to only take five rows.",
               task="Try typing: SELECT * FROM products LIMIT 5;",
               exp="SELECT * FROM products LIMIT 5;",
               trick="SELECT * + LIMIT = a quick sample, fast to read.",
               hints=H("Show every column.", "The star does that.", "Limit the rows to five.",
                       "Type: SELECT * FROM products LIMIT 5;"),
            ),
            st("predict", "Predict the row count",
               "Numbers first, explanation after:\n"
               "SELECT * FROM products LIMIT 5;\n"
               "How many rows will it return?",
               task="How many rows does the result show?",
               check={"answer": ["5", "five", "5 rows", "five rows"]},
               hints=H("Look at the last word of the query.",
                       "LIMIT means 'stop after'.", "The number after LIMIT is the answer.",
                       "Answer: 5."),
               trick="The number after LIMIT is your row count."),
        ],
    }


# --------------------------------------------------------------------------
def L07():
    return {
        "id": "L07", "order": 7, "difficulty": 2, "tags": ["count", "aggregate"],
        "title": "COUNT: how many rows are there?",
        "steps": [
            st("fill", "COUNT(*) - the crowd counter",
               "COUNT(*) answers 'how many rows?' with one number.\n"
               "It's like a shopkeeper counting the jars on a shelf - one, two, three…\n"
               "SELECT ___(*) FROM products;",
               task="Fill the blank with the word for counting.",
               seed="SELECT ___(*) FROM products;",
               exp="SELECT count(*) FROM products;",
               hints=H("The star inside the brackets means 'every row'.", "The word starts with 'c'.",
                       "It's the same word as the title of this lesson.",
                       "Replace ___ with count."),
               trick="count(*) = 'how many rows?'",
            ),
            st("type", "Count with a filter",
               "COUNT combines beautifully with WHERE.\n"
               "Ask: 'how many customers live in Marrakech?'",
               task="Try typing: SELECT count(*) FROM customers WHERE city = 'Marrakech';",
               exp="SELECT count(*) FROM customers WHERE city = 'Marrakech';",
               trick="WHERE narrows first, COUNT counts what's left.",
               hints=H("Start with SELECT count(*) FROM customers.",
                       "Add WHERE city = …", "Wrap Marrakech in single quotes.",
                       "Type: SELECT count(*) FROM customers WHERE city = 'Marrakech';"),
            ),
            st("predict", "Predict the count",
               "Sales people often ask 'how many?':\n"
               "SELECT count(*) FROM sale_items WHERE quantity >= 2;\n"
               "(quantity >= 2 means 'bought two or more of this item').",
               task="How many items were sold in pairs or more?",
               check={"answer": ["70", "70 rows", "seventy"]},
               hints=H("Run the query - prediction lets you verify.",
                       "quantity >= 2 keeps rows where the number is 2, 3, 4…",
                       "It's between 60 and 80.",
                       "Answer: 70."),
               trick=">= means 'this much or more'."),
            st("answer", "NULL's little secret",
               "COUNT(*) counts every row, even ones with empty bits.\n"
               "COUNT(name) counts rows where name is NOT empty.\n"
               "An empty bit is called NULL (say 'null': nothing there).",
               task="In SQL, COUNT(name) skips rows where name is …",
               check={"answer": ["null", "empty", "missing", "missing (null)", "nothing",
                                 "missing value", "empty (null)"]},
               hints=H("It skips rows where the column has no value.",
                       "The special SQL word is four letters.",
                       "It looks like a mix of 'nil' and 'null'.",
                       "Answer: NULL."),
               trick="COUNT(column) skips NULLs; COUNT(*) skips nothing."),
            st("type", "Count the two-or-more",
               "Put it together for real - count the sale_items sold in pairs or more:",
               task="Try typing: SELECT count(*) FROM sale_items WHERE quantity >= 2;",
               exp="SELECT count(*) FROM sale_items WHERE quantity >= 2;",
               trick="count + where = 'how many rows pass the filter?'",
               hints=H("Start with SELECT count(*).", "Add FROM sale_items.",
                       "Finish with WHERE quantity >= 2.",
                       "Type: SELECT count(*) FROM sale_items WHERE quantity >= 2;"),
            ),
        ],
    }


# --------------------------------------------------------------------------
def L08():
    return {
        "id": "L08", "order": 8, "difficulty": 3, "tags": ["group by", "aggregate"],
        "title": "GROUP BY: bundling rows into piles",
        "steps": [
            st("fill", "Piles by category",
               "GROUP BY splits rows into piles that share something.\n"
               "'How many products live in each category?' - each category becomes one pile, and count(*) counts the pile.\n"
               "SELECT category_id, count(*) FROM products GROUP BY ___;",
               task="Fill the blank with the column we group the piles by.",
               seed="SELECT category_id, count(*) FROM products GROUP BY ___;",
               exp="SELECT category_id, count(*) FROM products GROUP BY category_id;",
               hints=H("We pile products by…", "The piles are the categories.",
                       "Each category has an id number.",
                       "Replace ___ with category_id."),
               trick="GROUP BY = 'make a pile for each…'"),
            st("type", "Run the piles",
               "Type the pile query for real. The Output pane shows one row per category, with its count.",
               task="Try typing: SELECT category_id, count(*) FROM products GROUP BY category_id;",
               exp="SELECT category_id, count(*) FROM products GROUP BY category_id;",
               trick="One output row per pile.",
               hints=H("Start with SELECT category_id, count(*).",
                       "Add FROM products.", "Finish with GROUP BY category_id.",
                       "Type: SELECT category_id, count(*) FROM products GROUP BY category_id;"),
            ),
            st("fix", "Fix the missing GROUP BY",
               "Someone forgot the rules of piles:\n"
               "SELECT category_id, count(*) FROM products;\n"
               "The database complains: mixing per-row values with the grand total is confusing.",
               task="Fix it by adding the missing GROUP BY.",
               seed="SELECT category_id, count(*) FROM products;",
               exp="SELECT category_id, count(*) FROM products GROUP BY category_id;",
               hints=H("The error is about mixing a column with an aggregate.",
                       "One pile per category_id makes it legal.",
                       "Add a clause after FROM products.",
                       "Fix by appending GROUP BY category_id."),
               trick="Aggregates get lonely: give them a GROUP BY."),
            st("type", "SUM - money piles",
               "COUNT counts; SUM adds. 'What is each category worth?'\n"
               "SUM(price) adds all the prices in each pile.",
               task="Try typing: SELECT category_id, sum(price) FROM products GROUP BY category_id;",
               exp="SELECT category_id, sum(price) FROM products GROUP BY category_id;",
               trick="sum(price) = 'add up the prices in each pile'.",
               hints=H("Start with SELECT category_id, sum(price).",
                       "Add FROM products.", "Group by category_id.",
                       "Type: SELECT category_id, sum(price) FROM products GROUP BY category_id;"),
            ),
             st("predict", "Predict the biggest pile",
                "Each pile from GROUP BY can be turned back into a name with a JOIN:\n"
                "SELECT c.name, count(*) AS n FROM products p JOIN categories c ON p.category_id = c.id GROUP BY c.name;\n"
                "The pile with the highest count holds the most products.",
                task="Which category has the most products?",
                check={"answer": ["spices & herbs", "spices and herbs", "spices", "spices and herb"]},
                hints=H("The biggest count is 8.", "The names come from the categories table.",
                        "It's where ras el hanout and saffron live.",
                        "Answer: Spices & Herbs."),
                trick="Read piles like a top-ten chart."),
        ],
    }


# --------------------------------------------------------------------------
def L09():
    return {
        "id": "L09", "order": 9, "difficulty": 3, "tags": ["join", "inner join"],
        "title": "JOIN: gluing two tables together",
        "steps": [
            st("type", "The glue word: JOIN",
               "Products only have a category NUMBER (category_id) - the name lives in another table.\n"
               "JOIN glues two tables side by side by matching keys, like puzzle pieces.\n"
               "ON p.category_id = c.id is the instruction: 'glue where the product's category number matches the category's own number.'",
               task="Try typing: SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id;",
               exp="SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id;",
               trick="JOIN = glue; ON = where to glue.",
               hints=H("Short names p and c are nicknames for the tables.",
                       "ON tells SQL which columns to match.",
                       "Products carry category_id; categories carry id.",
                       "Type the JOIN with ON p.category_id = c.id."),
            ),
            st("fill", "Fill the ON",
               "The glue needs its matching instruction. Fill the blank:\n"
               "SELECT p.name, c.name FROM products p JOIN categories c ON ___.category_id = ___.id;",
               task="Fill both blanks with the table nicknames.",
               seed="SELECT p.name, c.name FROM products p JOIN categories c ON ___.category_id = ___.id;",
               exp="SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id;",
               hints=H("The nicknames are p and c.", "The first condition is about products.",
                       "Product's column is category_id; the category's is id.",
                       "Fill with p then c."),
               trick="ON = 'match these two keys'."),
            st("type", "Sales need names",
               "Invoices record customer NUMBERS, not names. JOIN brings the names in:\n"
               "SELECT s.id, c.name FROM sales s JOIN customers c ON s.customer_id = c.id;",
               task="Try typing: SELECT s.id, c.name FROM sales s JOIN customers c ON s.customer_id = c.id;",
               exp="SELECT s.id, c.name FROM sales s JOIN customers c ON s.customer_id = c.id;",
               trick="Keys in one table become names when you JOIN.",
               hints=H("Nickname sales as s and customers as c.",
                       "ON matches customer_id to id.",
                       "Show the sale id and the customer's name.",
                       "Type: SELECT s.id, c.name FROM sales s JOIN customers c ON s.customer_id = c.id;"),
            ),
            st("predict", "Predict the row count",
               "There are 45 sales and 30 customers. JOIN matches every sale to one customer.\n"
               "SELECT count(*) FROM sales s JOIN customers c ON s.customer_id = c.id;",
               task="How many rows does the join return?",
               check={"answer": ["45", "forty five", "45 rows"]},
               hints=H("Each sale glues to exactly one customer.",
                       "There are 45 sales.",
                       "No sale is left behind in an inner join.",
                       "Answer: 45."),
               trick="INNER JOIN keeps only rows that find a partner."),
            st("type", "Products with real category names",
               "Final puzzle piece - switch the numbers for names on the full products list:",
               task="Try typing: SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id;",
               exp="SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id;",
               trick="From now on, JOIN is your everyday friend.",
               hints=H("Join products p to categories c.",
                       "ON p.category_id = c.id.",
                       "Show p.name and c.name.",
                       "Write: SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id;"),
            ),
        ],
    }


# --------------------------------------------------------------------------
def L10():
    return {
        "id": "L10", "order": 10, "difficulty": 3, "tags": ["left join", "null"],
        "title": "LEFT JOIN: keeping lonely rows",
        "steps": [
            st("type", "The lonely product",
               "An INNER JOIN throws away rows without a partner.\n"
               "LEFT JOIN keeps every row of the LEFT table, even partnerless ones.\n"
               "Find the product nobody ever sold: its sale_items row just won't exist (NULL).",
               task="Try typing: SELECT p.name, si.sale_id FROM products p LEFT JOIN sale_items si ON si.product_id = p.id WHERE si.sale_id IS NULL;",
               exp="SELECT p.name, si.sale_id FROM products p LEFT JOIN sale_items si ON si.product_id = p.id WHERE si.sale_id IS NULL;",
               trick="LEFT JOIN = 'keep everyone on the left side'.",
               hints=H("Products are the LEFT table here.",
                       "A never-sold product has no sale_items row.",
                       "IS NULL finds the gaps.",
                       "Write the LEFT JOIN with WHERE si.sale_id IS NULL."),
            ),
            st("type", "The twenty quiet customers",
               "Same trick, new heroes: which customers have never ordered?\n"
               "Their sales row is missing.",
               task="Try typing: SELECT c.name, s.id AS sale_id FROM customers c LEFT JOIN sales s ON s.customer_id = c.id WHERE s.id IS NULL;",
               exp="SELECT c.name, s.id AS sale_id FROM customers c LEFT JOIN sales s ON s.customer_id = c.id WHERE s.id IS NULL;",
               trick="AS gives a column a nicer name for reading.",
               hints=H("Customers go LEFT, sales go RIGHT.",
                       "Match s.customer_id to c.id.",
                       "Keep only the rows where s.id is missing.",
                       "Write the LEFT JOIN and filter with WHERE s.id IS NULL."),
            ),
            st("answer", "What does LEFT mean?",
               "In FROM customers c LEFT JOIN sales s, every customer is kept - even ones with no sales.\n"
               "A customer with no sales shows NULL for the sales columns. INNER JOIN would hide those rows entirely.",
               task="Which table's rows are ALL kept by a LEFT JOIN?",
               check={"answer": ["the left table", "left table", "the table on the left",
                                 "products", "the first table", "the table written before join"]},
               hints=H("The name hides the answer.", "'LEFT' points at the first table written.",
                       "In FROM customers c LEFT JOIN sales s, it's customers.",
                       "Answer: the left (first) table."),
               trick="LEFT = love your left table unconditionally."),
            st("predict", "Predict: INNER vs LEFT",
               "In the shop there is 1 never-sold product and 20 customers without orders.\n"
               "SELECT count(*) FROM products p INNER JOIN sale_items si ON si.product_id = p.id;\n"
               "What does the INNER JOIN return?",
               task="How many rows (products with at least one sale)?",
               check={"answer": ["39", "39 rows", "thirty nine"]},
               hints=H("INNER JOIN drops lonely rows.",
                       "40 products, 1 never sold.",
                       "40 minus 1.",
                       "Answer: 39."),
               trick="INNER drops the lonely; LEFT keeps them."),
        ],
    }


LESSONS = [L01(), L02(), L03(), L04(), L05(), L06(), L07(), L08(),
           L09(), L10()]