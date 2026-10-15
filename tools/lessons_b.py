"""Lessons L11-L20: changing data, building tables, and the advanced world."""

from tools.lessons_a import H, st


# --------------------------------------------------------------------------
def L11():
    return {
        "id": "L11", "order": 11, "difficulty": 3, "tags": ["insert", "write"],
        "title": "INSERT: adding a new row",
        "steps": [
            st("type", "The friendly new customer",
               "So far we only READ. INSERT ADDS a row - like a guest book getting a new signature.\n"
               "You name the columns, then list the VALUES in the same order.",
               task="Try typing: INSERT INTO customers (name, email, city, created_at) VALUES ('Amina', 'amina@shop.ma', 'Rabat', '2026-05-01');",
               exp="INSERT INTO customers (name, email, city, created_at) VALUES ('Amina', 'amina@shop.ma', 'Rabat', '2026-05-01');",
               trick="INSERT INTO = 'add to…', VALUES = 'these are the facts'.",
               hints=H("Start with INSERT INTO customers.",
                       "List the columns you're filling in brackets.",
                       "VALUES holds the facts, in the same order.",
                       "Write the full INSERT with 'Amina' first."),
            ),
            st("type", "Add a product",
               "Practice the muscle memory - add a fresh jar of argan oil:\n"
               "INSERT INTO products (name, category_id, supplier_id, price, stock, created_at) VALUES ('Argan Oil 250ml', 2, 1, 149.99, 12, '2026-05-02');",
               task="Try typing the INSERT for the argan oil.",
               exp="INSERT INTO products (name, category_id, supplier_id, price, stock, created_at) VALUES ('Argan Oil 250ml', 2, 1, 149.99, 12, '2026-05-02');",
               trick="Column list and value list must march in the same order.",
               hints=H("It's an INSERT INTO products query.",
                       "Fill the columns: name, category_id, supplier_id, price, stock, created_at.",
                       "The values come in brackets after VALUES.",
                       "Watch the quotes around text and the commas between values."),
            ),
            st("fill", "Fill the values",
               "Your turn to invent one fact at a time. Fill the blanks:\n"
               "INSERT INTO customers (name, city) VALUES (___, ___);",
               task="Add the customer Yasmine from Casablanca.",
               seed="INSERT INTO customers (name, city) VALUES (___, ___);",
               exp="INSERT INTO customers (name, city) VALUES ('Yasmine', 'Casablanca');",
               hints=H("Two columns, two values.",
                       "Text needs single quotes.",
                       "Name comes first, then city.",
                       "Fill: 'Yasmine', 'Casablanca'."),
               trick="Every value keeps its own quote-needing or bare nature."),
             st("predict", "Predict the missing email",
                "This INSERT fills only name and city:\n"
                "INSERT INTO customers (name, city) VALUES ('Omar', 'Tangier');\n"
                "The email column is left out. The table lets email be missing (it's nullable).\n"
                "What value fills the empty email?",
                task="What's the special word for 'this value is missing'?",
                check={"answer": ["null", "missing", "empty", "nothing", "no value"]},
                hints=H("You've met this word in the COUNT lesson.",
                        "It's the word for 'no value there'.",
                        "Four letters, starts with n.",
                        "Answer: NULL."),
                trick="NULL = the honest way to say 'nothing here'."),
            st("type", "Add and check",
               "Final run - insert, then immediately SELECT to see the new row:\n"
               "INSERT INTO customers (name, city) VALUES ('Yasmine', 'Casablanca');\n"
               "SELECT name, city FROM customers WHERE name = 'Yasmine';",
               task="Run the INSERT, then the SELECT.",
               exp="INSERT INTO customers (name, city) VALUES ('Yasmine', 'Casablanca');\nSELECT name, city FROM customers WHERE name = 'Yasmine';",
               check={"ordered": False},
               trick="Write first, verify second - always.",
               hints=H("Two statements, separated by a new line.",
                       "First add Yasmine.",
                       "Then look her up with WHERE name = 'Yasmine'.",
                       "Run INSERT first and SELECT second."),
            ),
        ],
    }


# --------------------------------------------------------------------------
def L12():
    return {
        "id": "L12", "order": 12, "difficulty": 3, "tags": ["update", "write"],
        "title": "UPDATE: changing what's already there",
        "steps": [
            st("type", "Self-service: top up stock",
               "UPDATE rewrites values in EXISTING rows - like topping up the honey jar.\n"
               "SET stock = stock + 10 says 'the new stock is the old stock plus ten'.",
               task="Try typing: UPDATE products SET stock = stock + 10 WHERE id = 1;",
               exp="UPDATE products SET stock = stock + 10 WHERE id = 1;",
               trick="SET = 'change this column to…'",
               hints=H("Start with UPDATE products.",
                       "SET names the column to change.",
                       "stock + 10 adds ten to the old value.",
                       "Write: UPDATE products SET stock = stock + 10 WHERE id = 1;"),
            ),
            st("type", "A 10% price rise",
               "Sometimes a whole category gets a price rise.\n"
               "UPDATE … SET price = price * 1.1 … hits every matching row at once.",
               task="Try typing: UPDATE products SET price = price * 1.1 WHERE category_id = 5;",
               exp="UPDATE products SET price = price * 1.1 WHERE category_id = 5;",
               trick="One UPDATE, many rows - the WHERE decides how many.",
               hints=H("UPDATE products SET …",
                       "Multiply the old price: price * 1.1.",
                       "Only category 5 should change.",
                       "Write: UPDATE products SET price = price * 1.1 WHERE category_id = 5;"),
            ),
            st("fill", "Fix one price",
               "One product has a wrong price. Fill the SET clause:\n"
               "UPDATE products SET ___ WHERE id = 2;",
               task="Set the price of product id 2 to 24.99.",
               seed="UPDATE products SET ___ WHERE id = 2;",
               exp="UPDATE products SET price = 24.99 WHERE id = 2;",
               hints=H("The change is about money.", "The column is price.",
                       "The new value is 24.99.",
                       "Fill: price = 24.99"),
               trick="SET column = new value - that's the whole medicine."),
            st("predict", "Predict the forgetful UPDATE",
               "If someone writes UPDATE products SET stock = 0; (no WHERE at all)…\n"
               "What happens to the 40 rows?",
               task="How many products end up with zero stock?",
               check={"answer": ["40", "all 40", "40 rows", "every row", "all of them"]},
               hints=H("No WHERE means no filtering.",
                       "The UPDATE touches every row it can.",
                       "There are 40 products.",
                       "Answer: all 40."),
               trick="No WHERE = every row. That's why safety warnings exist."),
            st("answer", "The safety habit",
               "You'll see a friendly warning before UPDATE/DELETE that touches many rows.\n"
               "It's not a scolding - it's a check-in, because the practice shop is YOURS to test.\n"
               "Reset (the ↺ button) always brings everything back.",
               task="What does the ↺ Reset button do?",
               check={"answer": ["restores the original data", "puts everything back",
                                 "restores the original shop", "undoes my changes",
                                 "resets the database"]},
               hints=H("Look at the little arrow button near the output.",
                       "It looks like the redo/refresh symbol.",
                       "It brings back the shop you started with.",
                       "Answer: restores the original data."),
               trick="Reset = always your safety net."),
        ],
    }


# --------------------------------------------------------------------------
def L13():
    return {
        "id": "L13", "order": 13, "difficulty": 3, "tags": ["delete", "write"],
        "title": "DELETE: removing rows",
        "steps": [
            st("type", "Say goodbye nicely",
               "DELETE removes rows - like crossing a name off a guest list.\n"
               "Always use WHERE, so only the intended row goes.",
               task="Try typing: DELETE FROM customers WHERE name = 'Khadija Sabri';",
               exp="DELETE FROM customers WHERE name = 'Khadija Sabri';",
               trick="DELETE FROM + WHERE = 'remove exactly these rows'.",
               hints=H("Start with DELETE FROM customers.",
                       "Name the customer you want to remove.",
                       "Use WHERE with the name in quotes.",
                       "Write: DELETE FROM customers WHERE name = 'Khadija Sabri';"),
            ),
            st("fill", "Delete by id",
               "Rows are safer to delete by their ID - it's unique. Fill the blank:\n"
               "DELETE FROM customers WHERE id = ___;",
               task="Delete the customer with id 12.",
               seed="DELETE FROM customers WHERE id = ___;",
               exp="DELETE FROM customers WHERE id = 12;",
               hints=H("WHERE picks the row.", "We delete the one with id 12.",
                       "The blank is a number.",
                       "Fill: 12"),
               trick="id = the row's unique fingerprint."),
            st("predict", "Predict the scariest DELETE",
               "What does this do?\n"
               "DELETE FROM products;",
               task="How many rows are removed?",
               check={"answer": ["40", "all of them", "all 40", "every row", "all rows"]},
               hints=H("There's no WHERE anywhere.",
                       "An unfiltered DELETE clears the whole table.",
                       "The products table has 40 rows.",
                       "Answer: all 40."),
               trick="DELETE without WHERE = the whole table. You'll be warned first."),
            st("answer", "Why the warning?",
               "Real databases can't be Reset. In a real shop, DELETE FROM products; would empty the shelves for good.\n"
               "That's why the app gently warns you - and why you practice so a real DELETE never surprises you.",
               task="In a REAL (non-practice) database, what happens to DELETEd rows?",
               check={"answer": ["they are gone for good", "they are gone", "they disappear",
                                 "they're gone permanently", "permanently deleted"]},
               hints=H("There's no Reset button in real life.",
                       "Think of a paper register being cut up.",
                       "The rows are removed from the table.",
                       "Answer: gone for good."),
               trick="Practice habits become real-world safety."),
        ],
    }


# --------------------------------------------------------------------------
def L14():
    return {
        "id": "L14", "order": 14, "difficulty": 3, "tags": ["create", "ddl"],
        "title": "CREATE TABLE: making a new home for data",
        "steps": [
            st("fill", "The table recipe",
               "So far the tables were given to us. CREATE TABLE builds a new one.\n"
               "You name the table, then list columns: name TYPE.\n"
               "CREATE TABLE favorites (id INTEGER PRIMARY KEY, product_name ___);",
               task="Fill the blank with the type for text.",
               seed="CREATE TABLE favorites (id INTEGER PRIMARY KEY, product_name ___);",
               exp="CREATE TABLE favorites (id INTEGER PRIMARY KEY, product_name TEXT);",
               hints=H("product_name holds words.", "The type for words is four letters.",
                       "INTEGER is for numbers; this one starts with T.",
                       "Fill: TEXT"),
               trick="TEXT holds words, INTEGER holds numbers, REAL holds decimal numbers."),
            st("type", "Build and admire",
               "CREATE TABLE IF NOT EXISTS says 'only make it if it isn't already made' - safe to run twice.\n"
               "Build the wishlist box for your favourite products.",
               task="Try typing: CREATE TABLE IF NOT EXISTS wishlist (id INTEGER PRIMARY KEY, name TEXT, price REAL);",
               exp="CREATE TABLE IF NOT EXISTS wishlist (id INTEGER PRIMARY KEY, name TEXT, price REAL);",
               trick="IF NOT EXISTS = 'don't break if it's already there'.",
               hints=H("Start with CREATE TABLE IF NOT EXISTS wishlist.",
                       "Inside the brackets: id INTEGER PRIMARY KEY.",
                       "Then name TEXT, then price REAL.",
                       "Write the full CREATE statement."),
            ),
            st("predict", "Predict the PRIMARY KEY",
               "PRIMARY KEY id does two jobs at once:\n"
               "1. every row gets a unique number\n"
               "2. the database finds rows fast.",
               task="What makes each row's id number unique?",
               check={"answer": ["primary key", "the primary key", "unique"]},
               hints=H("It's not just any column - it's special.",
                       "Two words, both in your CREATE statement.",
                       "'PRIMARY' means top, 'KEY' means the one that opens the row.",
                       "Answer: PRIMARY KEY."),
               trick="PRIMARY KEY = unique identity card per row."),
            st("type", "Make the empty home feel alive",
               "Now fill it with one row:\n"
               "CREATE TABLE IF NOT EXISTS wishlist (id INTEGER PRIMARY KEY, name TEXT, price REAL);\n"
               "INSERT INTO wishlist (name, price) VALUES ('Beni Ourain Rug', 3356.82);",
               task="Run the CREATE then the INSERT.",
               exp="CREATE TABLE IF NOT EXISTS wishlist (id INTEGER PRIMARY KEY, name TEXT, price REAL);\nINSERT INTO wishlist (name, price) VALUES ('Beni Ourain Rug', 3356.82);",
               trick="CREATE the shape, INSERT the life.",
               hints=H("Two statements, one after the other.",
                       "First: CREATE TABLE IF NOT EXISTS wishlist (id INTEGER PRIMARY KEY, name TEXT, price REAL);",
                       "Then INSERT INTO wishlist (name, price).",
                       "Run CREATE first, INSERT second."),
            ),
        ],
    }


# --------------------------------------------------------------------------
def L15():
    return {
        "id": "L15", "order": 15, "difficulty": 4, "tags": ["case", "having"],
        "title": "CASE and HAVING: labels and group filters",
        "steps": [
            st("type", "CASE: if-this-then-that labels",
               "CASE makes a new column from rules, like a price tag sticker: 'pricey' or 'ok'.\n"
               "WHEN the rule fits, THEN the value; ELSE is the fallback; END closes it.",
               task="Try typing: SELECT name, price, CASE WHEN price > 300 THEN 'pricey' ELSE 'ok' END AS tag FROM products;",
               exp="SELECT name, price, CASE WHEN price > 300 THEN 'pricey' ELSE 'ok' END AS tag FROM products;",
               trick="CASE = 'decide as you go, row by row'.",
               hints=H("SELECT name, price, then the CASE.",
                       "CASE WHEN price > 300 THEN 'pricey'.",
                       "ELSE 'ok' covers the rest, END finishes.",
                       "Write the compact CASE expression and alias it AS tag."),
            ),
            st("fill", "Fill the CASE elbow",
               "Fill the blank so expensive products get the 'luxury' label:\n"
               "SELECT name, CASE WHEN price > 1000 THEN 'luxury' ___ 'standard' END FROM products;",
               task="Fill the blank with the else-word.",
               seed="SELECT name, CASE WHEN price > 1000 THEN 'luxury' ___ 'standard' END FROM products;",
               exp="SELECT name, CASE WHEN price > 1000 THEN 'luxury' ELSE 'standard' END FROM products;",
               hints=H("THEN gives the true-case value.",
                       "The else-case word is four letters.",
                       "It sits between the two labels.",
                       "Fill: ELSE"),
               trick="WHEN … THEN … ELSE … END - the full decision recipe."),
            st("type", "HAVING: a WHERE for piles",
               "WHERE filters ROWS. HAVING filters PILES (groups).\n"
               "Find the categories with more than five products.",
               task="Try typing: SELECT category_id, count(*) AS c FROM products GROUP BY category_id HAVING c > 5;",
               exp="SELECT category_id, count(*) AS c FROM products GROUP BY category_id HAVING c > 5;",
               trick="HAVING = the WHERE of the GROUP BY world.",
               hints=H("Build the GROUP BY query first.",
                       "count(*) AS c gives the count a name.",
                       "HAVING c > 5 filters the piles.",
                       "Write the GROUP BY … HAVING query."),
            ),
            st("predict", "Predict the pile filter",
               "This query piles products by category, then keeps only the big piles:\n"
               "SELECT category_id, count(*) FROM products GROUP BY category_id HAVING count(*) > 5;\n"
               "Product counts per category_id are: 8, 5, 5, 5, 5, 5, 3, 4.\n"
               "With HAVING count(*) > 5, only ONE pile survives.",
               task="Which category_id survives the HAVING?",
               check={"answer": ["1", "category 1", "category_id 1"]},
               hints=H("Candidates: which count is above 5?",
                       "Only one pile has more than 5 products - it has 8.",
                       "That pile is category_id 1.",
                       "Answer: 1."),
               trick="HAVING shaves the chart to the tall bars."),
        ],
    }


# --------------------------------------------------------------------------
def L16():
    return {
        "id": "L16", "order": 16, "difficulty": 4, "tags": ["subquery"],
        "title": "Subqueries: a query inside a query",
        "steps": [
            st("type", "The librarian's reference book",
               "A subquery is a query inside brackets, used like a value or a mini-table.\n"
               "Find products above the AVERAGE price: the average is itself a query.",
               task="Try typing: SELECT name, price FROM products WHERE price > (SELECT avg(price) FROM products);",
               exp="SELECT name, price FROM products WHERE price > (SELECT avg(price) FROM products);",
               trick="(SELECT … ) = ask the database first, then use the answer.",
               hints=H("The inner SELECT computes the average.",
                       "avg(price) is the shop's mean price.",
                       "The outer query compares price to it.",
                       "Write the WHERE with the bracketed subquery."),
            ),
            st("fill", "Fill the mini-query",
               "Fill the blank to find the most expensive product:\n"
               "SELECT name, price FROM products WHERE price = (SELECT ___ FROM products);",
               task="Fill the blank with the function that returns the biggest value.",
               seed="SELECT name, price FROM products WHERE price = (SELECT ___ FROM products);",
               exp="SELECT name, price FROM products WHERE price = (SELECT max(price) FROM products);",
               hints=H("We want 'the biggest price'.", "Its function starts with 'ma'.",
                       "min is the other way round.",
                       "Fill: max(price)"),
               trick="max/min/avg/count are your pocket answers for comparisons."),
            st("type", "The other side of average",
               "The subquery gives the shop's average price; this query keeps the products BELOW it.\n"
               "Flip the operator to < to see the cheaper half.",
               task="Try typing: SELECT name, price FROM products WHERE price < (SELECT avg(price) FROM products);",
               exp="SELECT name, price FROM products WHERE price < (SELECT avg(price) FROM products);",
               trick="Subqueries turn 'compare to a number' into 'compare to a fact'.",
               hints=H("The inner bracket-pair is the average.",
                       "The outer part keeps price < average.",
                       "Compare with the less-than operator <.",
                       "Write SELECT name, price FROM products WHERE price < (SELECT avg(price) FROM products);"),
            ),
            st("answer", "Why the brackets?",
               "Brackets tell SQL: 'resolve this piece first, then continue with my main question.'\n"
               "Without them, SQL reads the sentence in the wrong order.\n"
               "(Also: run the mini-query alone - SELECT avg(price) FROM products - just for the feel.)",
               task="What do the round brackets do around the inner query?",
               check={"answer": ["ask first, then use the answer", "it runs first",
                                 "the inner query runs first", "ask the inner question first",
                                 "they run the inner query first"]},
               hints=H("Think of maths: (2 + 3) * 4 …",
                       "The part in brackets is resolved before the rest.",
                       "So the average is known before comparing.",
                       "Answer: it runs first, and its answer gets used."),
               trick="Brackets = 'do this bit first'."),
        ],
    }


# --------------------------------------------------------------------------
def L17():
    return {
        "id": "L17", "order": 17, "difficulty": 4, "tags": ["cte", "with"],
        "title": "WITH: giving your subquery a name",
        "steps": [
            st("type", "Name your table-on-the-fly",
               "A CTE (say: 'see-tee-ee') is a subquery with a NAME, written at the top with WITH.\n"
               "It's like sketching the plan on a napkin before writing the menu.",
               task="Try typing: WITH busy AS (SELECT category_id, count(*) AS c FROM products GROUP BY category_id) SELECT * FROM busy WHERE c > 5;",
               exp="WITH busy AS (SELECT category_id, count(*) AS c FROM products GROUP BY category_id) SELECT * FROM busy WHERE c > 5;",
               trick="WITH name AS (…) = 'here's a temporary list, call it this'.",
               hints=H("WITH introduces the temporary list.",
                       "busy AS wraps the GROUP BY query.",
                       "Then a plain SELECT reads FROM busy.",
                       "Filter the named list with WHERE c > 5."),
            ),
            st("fill", "Fill the temporary name",
               "Fill the blank with a name for the temporary list:\n"
               "WITH ___ AS (SELECT category_id, count(*) AS c FROM products GROUP BY category_id) SELECT * FROM ___ WHERE c = 3;",
               task="Use the same name in both blanks.",
               seed="WITH ___ AS (SELECT category_id, count(*) AS c FROM products GROUP BY category_id) SELECT * FROM ___ WHERE c = 3;",
               exp="WITH cheap AS (SELECT category_id, count(*) AS c FROM products GROUP BY category_id) SELECT * FROM cheap WHERE c = 3;",
               hints=H("The name is yours to invent.",
                       "Both blanks must hold the same word.",
                       "This list holds category counts.",
                       "Fill both with 'cheap'."),
               trick="Same name twice: once created, once used."),
            st("answer", "Why bother with WITH?",
               "WITH makes long questions readable: name the messy part once, use it after.\n"
               "It also lets you reuse the same list later in the same query - no copy-paste.",
               task="What is the temporary list called in SQL?",
               check={"answer": ["cte", "a cte", "common table expression", "a common table expression"]},
               hints=H("The letters C-T-E …",
                       "It starts with 'Common'.",
                       "'Table Expression' - like a mini table.",
                       "Answer: CTE (Common Table Expression)."),
               trick="CTE = a named napkin sketch you can reuse."),
        ],
    }


# --------------------------------------------------------------------------
def L18():
    return {
        "id": "L18", "order": 18, "difficulty": 5, "tags": ["window", "rank"],
        "title": "Window functions: ranking without losing the rows",
        "steps": [
            st("type", "ROW_NUMBER over a window",
               "So far every row kept its own facts. A window function looks at a WINDOW of rows around each row and computes with them - like a medal table.\n"
               "ROW_NUMBER() OVER (ORDER BY price DESC) numbers rows from the most expensive down.",
               task="Try typing: SELECT name, price, ROW_NUMBER() OVER (ORDER BY price DESC) AS pos FROM products LIMIT 5;",
               exp="SELECT name, price, ROW_NUMBER() OVER (ORDER BY price DESC) AS pos FROM products LIMIT 5;",
               trick="OVER = 'window over these sorted rows'.",
               hints=H("Pick name, price, and the ranking column.",
                       "ROW_NUMBER() OVER (ORDER BY price DESC).",
                       "Alias the ranking AS pos.",
                       "Finish with LIMIT 5."),
            ),
            st("fill", "Fill the function with the sharers",
               "RANK() is smarter than ROW_NUMBER(): equal prices share a rank, then it skips the gap.\n"
               "Fill the blank:\n"
               "SELECT name, price, ___() OVER (ORDER BY price DESC) AS r FROM products LIMIT 5;",
               task="Fill the blank with the sharing-rank function.",
               seed="SELECT name, price, ___() OVER (ORDER BY price DESC) AS r FROM products LIMIT 5;",
               exp="SELECT name, price, RANK() OVER (ORDER BY price DESC) AS r FROM products LIMIT 5;",
               hints=H("ROW_NUMBER never shares - this one does.",
                       "It's four letters.",
                       "Row_number → the friendlier cousin.",
                       "Fill: RANK"),
               trick="RANK shares ties; ROW_NUMBER breaks them arbitrarily."),
            st("answer", "Why 'window'?",
               "There's a third famous one: DENSE_RANK() - ties share, and numbering never skips.\n"
               "These are called WINDOW functions because each row looks at the window of rows around it (sorted), not just itself.",
               task="What sorts the window in the OVER clause?",
               check={"answer": ["order by", "over (order by …)", "the order by clause",
                                 "order by price desc"]},
               hints=H("Look inside the OVER brackets.",
                       "The window slides across sorted rows.",
                       "The sorting words start with 'Order'.",
                       "Answer: ORDER BY."),
               trick="OVER (ORDER BY …) = slide across this order."),
        ],
    }


# --------------------------------------------------------------------------
def L19():
    return {
        "id": "L19", "order": 19, "difficulty": 4, "tags": ["transaction", "rollback"],
        "title": "Transactions: an undo button for the shop",
        "steps": [
            st("type", "BEGIN, break, ROLLBACK",
               "A TRANSACTION is a group of steps that either ALL happen, or NONE do - like baking: all or nothing.\n"
               "BEGIN opens a transaction. ROLLBACK rewinds everything since BEGIN.",
               task="Try typing the rewind demo:\nBEGIN; UPDATE products SET stock = 0; ROLLBACK; SELECT count(*) FROM products WHERE stock = 0;",
               exp="BEGIN; UPDATE products SET stock = 0; ROLLBACK; SELECT count(*) FROM products WHERE stock = 0;",
               trick="ROLLBACK = 'rewind to the last checkpoint'.",
               hints=H("Four statements, one after another.",
                       "BEGIN opens the transaction.",
                       "The UPDATE sneaks in a disaster, ROLLBACK undoes it.",
                       "The final SELECT shows zero damaged rows."),
            ),
            st("answer", "ROLLBACK guessed?",
               "Run this: BEGIN; UPDATE products SET stock = 0; ROLLBACK; SELECT count(*) FROM products WHERE stock = 0;\n"
               "The final SELECT returns 7, not 40 - because stock = 0 already existed for seven products.\n"
               "ROLLBACK undid the mass change. Without ROLLBACK, all 40 products would have been zeroed.",
               task="What undoes everything done since BEGIN?",
               check={"answer": ["rollback", "rollback;", "the rollback command"]},
               hints=H("It means 'rewind'.",
                       "It comes after a disaster.",
                       "It's written as one word after the broken UPDATE.",
                       "Answer: ROLLBACK."),
               trick="BEGIN…ROLLBACK = your safety rewind."),
            st("type", "SAVEPOINT: a midway bookmark",
               "SAVEPOINT drops a bookmark; ROLLBACK TO jumps back to it.\n"
               "Try: mark the clean state, make a mess, rewind to the mark.",
               task="Try typing: SAVEPOINT before_tweak; UPDATE products SET price = price * 2 WHERE id = 1; ROLLBACK TO before_tweak; SELECT price FROM products WHERE id = 1;",
               exp="SAVEPOINT before_tweak; UPDATE products SET price = price * 2 WHERE id = 1; ROLLBACK TO before_tweak; SELECT price FROM products WHERE id = 1;",
               trick="SAVEPOINT = bookmark, ROLLBACK TO = jump back to it.",
               hints=H("SAVEPOINT before_tweak marks the clean state.",
                       "The UPDATE doubles product 1's price.",
                       "ROLLBACK TO before_tweak jumps back.",
                       "The SELECT confirms the original price returned."),
            ),
            st("predict", "Predict the final price",
               "Run this and watch the price go out and come back:\n"
               "SAVEPOINT before_tweak; UPDATE products SET price = price * 2 WHERE id = 1; ROLLBACK TO before_tweak; SELECT price FROM products WHERE id = 1;\n"
               "The doubling is undone by ROLLBACK TO, so the final SELECT shows the original price.",
               task="What price shows at the end?",
               check={"answer": ["45.63", "45.63 mad", "the original price", "45.63 mad "]},
               hints=H("The ROLLBACK TO undid the doubling.",
                       "Product 1 started at 45.63.",
                       "The rewind restores exactly that.",
                       "Answer: 45.63."),
               trick="Rewinds are exact: the state returns, price and all."),
        ],
    }


# --------------------------------------------------------------------------
def L20():
    return {
        "id": "L20", "order": 20, "difficulty": 5, "tags": ["project", "mix"],
        "title": "Mini project: the shop's best-seller report",
        "steps": [
            st("type", "Report 1: the top 5 best-sellers",
               "Time to fly without a net. The boss wants the five best-selling products by quantity sold.\n"
               "You'll need: a JOIN (products × sale_items), SUM(quantity), GROUP BY, ORDER BY, LIMIT.",
               task="Try typing: SELECT p.name, sum(si.quantity) AS sold FROM products p JOIN sale_items si ON si.product_id = p.id GROUP BY p.name ORDER BY sold DESC LIMIT 5;",
               exp="SELECT p.name, sum(si.quantity) AS sold FROM products p JOIN sale_items si ON si.product_id = p.id GROUP BY p.name ORDER BY sold DESC LIMIT 5;",
               trick="Project recipe: JOIN → SUM → GROUP → ORDER → LIMIT.",
               hints=H("Join products p with sale_items si on product_id.",
                       "SUM(si.quantity) with alias sold.",
                       "GROUP BY p.name, then ORDER BY sold DESC.",
                       "LIMIT 5 finishes - the top row is Mini Tagine, 11 sold."),
            ),
            st("type", "Report 2: customers knocking, no one home",
               "The boss wants to reward loyal customers and gently re-engage the quiet ones.\n"
               "Find every customer with zero sales. (LEFT JOIN • IS NULL)",
               task="Try typing: SELECT c.name FROM customers c LEFT JOIN sales s ON s.customer_id = c.id WHERE s.id IS NULL ORDER BY c.name;",
               exp="SELECT c.name FROM customers c LEFT JOIN sales s ON s.customer_id = c.id WHERE s.id IS NULL ORDER BY c.name;",
               trick="LEFT JOIN + WHERE … IS NULL = 'the lonely ones'.",
               hints=H("Customers go on the LEFT.",
                       "Match s.customer_id = c.id.",
                       "Keep s.id IS NULL - sales that never happened.",
                       "ORDER BY c.name makes the list tidy."),
            ),
            st("type", "Report 3: how much each category earns",
               "Finally - money per category. Sale items carry unit_price and quantity; their product knows its category. That's a two-hop JOIN.",
               task="Try typing: SELECT c.name AS category, sum(si.unit_price * si.quantity) AS revenue FROM sale_items si JOIN products p ON p.id = si.product_id JOIN categories c ON c.id = p.category_id GROUP BY c.name ORDER BY revenue DESC;",
               exp="SELECT c.name AS category, sum(si.unit_price * si.quantity) AS revenue FROM sale_items si JOIN products p ON p.id = si.product_id JOIN categories c ON c.id = p.category_id GROUP BY c.name ORDER BY revenue DESC;",
               trick="Multi-hop JOIN: sale → product → category.",
               hints=H("Start from sale_items si.",
                       "Join p on p.id = si.product_id; join c on c.id = p.category_id.",
                       "Revenue = si.unit_price * si.quantity, summed.",
                       "Group by c.name, order by revenue DESC."),
            ),
            st("answer", "Project debrief",
               "You just ran a real business report: best-sellers, quiet customers, and category revenue.\n"
               "Every piece was built from small lessons: SELECT, JOIN, GROUP BY, ORDER BY, LIMIT.\n"
               "That's the whole secret - big queries are just small queries glued with new words.",
               task="Which building block did Report 1 use to rank products?",
               check={"answer": ["order by", "order by sold desc", "order by",
                                 "order by … desc"]},
               hints=H("Best-sellers = a ranking.",
                       "DESC puts the biggest on top.",
                       "The sort clause comes after GROUP BY.",
                       "Answer: ORDER BY."),
               trick="You're not memorising SQL - you're assembling it."),
        ],
    }


LESSONS = [L11(), L12(), L13(), L14(), L15(), L16(), L17(), L18(), L19(), L20()]