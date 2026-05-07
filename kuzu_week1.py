"""
ТИЖДЕНЬ 1: Перший граф у Kuzu
Завдання: граф "Мої проекти та технології"
"""
import kuzu

# ============================================================
# КРОК 1: Створити базу даних
# ============================================================
# Database("шлях") — створює папку з файлами бази
# Connection(db)   — з'єднання для виконання запитів (як cursor у SQLite)

db = kuzu.Database("./my_first_graph")
conn = kuzu.Connection(db)

print("✓ База даних створена")

# ============================================================
# КРОК 2: Визначити schema (схему) — структуру бази
# ============================================================
# NODE TABLE = тип вузла (як CREATE TABLE у SQL)
# PRIMARY KEY = унікальний ідентифікатор (не може бути два вузли з однаковим ключем)
# REL TABLE   = тип зв'язку між вузлами

conn.execute("CREATE NODE TABLE IF NOT EXISTS Person(name STRING, role STRING, PRIMARY KEY(name))")
conn.execute("CREATE NODE TABLE IF NOT EXISTS Project(name STRING, status STRING, PRIMARY KEY(name))")
conn.execute("CREATE NODE TABLE IF NOT EXISTS Technology(name STRING, category STRING, PRIMARY KEY(name))")

# FROM Person TO Project = зв'язок іде від Person до Project
# since = властивість самого зв'язку (не вузла!)
conn.execute("CREATE REL TABLE IF NOT EXISTS WORKS_ON(FROM Person TO Project, since INT64)")
conn.execute("CREATE REL TABLE IF NOT EXISTS USES(FROM Project TO Technology)")

print("✓ Schema створена")

# ============================================================
# КРОК 3: Додати вузли (nodes)
# ============================================================
# MERGE замість CREATE — безпечно запускати скільки завгодно разів:
# якщо вузол вже є → просто пропускає, якщо немає → створює

# Люди
conn.execute("MERGE (:Person {name: 'Євгеній', role: 'Director'})")
conn.execute("MERGE (:Person {name: 'Олена', role: 'Manager'})")
conn.execute("MERGE (:Project {name: 'САНЕКО сайт', status: 'planning'})")

# Проекти
conn.execute("MERGE (:Project {name: 'AgentRa', status: 'active'})")
conn.execute("MERGE (:Project {name: 'RAG Telegram Bot', status: 'active'})")
conn.execute("MERGE (:Project {name: 'KDP Coloring Book', status: 'active'})")

# Технології
conn.execute("MERGE (:Technology {name: 'n8n', category: 'automation'})")
conn.execute("MERGE (:Technology {name: 'Claude API', category: 'LLM'})")
conn.execute("MERGE (:Technology {name: 'FastAPI', category: 'backend'})")
conn.execute("MERGE (:Technology {name: 'Kuzu', category: 'graph_db'})")
conn.execute("MERGE (:Technology {name: 'ChromaDB', category: 'vector_db'})")
conn.execute("MERGE (:Technology {name: 'Python', category: 'language'})")
conn.execute("MERGE (:Technology {name: 'Telegram Bot API', category: 'messenger'})")

print("✓ Вузли додано")

# ============================================================
# КРОК 4: Додати зв'язки (edges)
# ============================================================
# Зв'язки не підтримують MERGE, тому спочатку видаляємо всі старі,
# потім створюємо заново — так файл можна запускати багато разів

# Спочатку видалити старі зв'язки (якщо є)
conn.execute("MATCH ()-[r:WORKS_ON]->() DELETE r")
conn.execute("MATCH ()-[r:USES]->() DELETE r")

# Євгеній працює над проектами
conn.execute("""
    MATCH (p:Person {name: 'Євгеній'}), (proj:Project {name: 'AgentRa'})
    CREATE (p)-[:WORKS_ON {since: 2024}]->(proj)
""")
conn.execute("""
    MATCH (p:Person {name: 'Євгеній'}), (proj:Project {name: 'RAG Telegram Bot'})
    CREATE (p)-[:WORKS_ON {since: 2025}]->(proj)
""")
conn.execute("""
    MATCH (p:Person {name: 'Євгеній'}), (proj:Project {name: 'KDP Coloring Book'})
    CREATE (p)-[:WORKS_ON {since: 2025}]->(proj)
""")
conn.execute("""
    MATCH (p:Person {name: 'Олена'}), (proj:Project {name: 'САНЕКО сайт'})
    CREATE (p)-[:WORKS_ON {since: 2026}]->(proj)
""")
conn.execute("""
    MATCH (proj:Project {name: 'САНЕКО сайт'}), (t:Technology {name: 'Python'})
    CREATE (proj)-[:USES]->(t)
""")
conn.execute("""
    MATCH (proj:Project {name: 'САНЕКО сайт'}), (t:Technology {name: 'FastAPI'})
    CREATE (proj)-[:USES]->(t)
""")

# Проекти використовують технології
uses = [
    ("AgentRa", "n8n"),
    ("AgentRa", "Claude API"),
    ("AgentRa", "FastAPI"),
    ("RAG Telegram Bot", "FastAPI"),
    ("RAG Telegram Bot", "Claude API"),
    ("RAG Telegram Bot", "ChromaDB"),
    ("RAG Telegram Bot", "Telegram Bot API"),
    ("KDP Coloring Book", "Python"),
    ("KDP Coloring Book", "n8n"),
]

for project, tech in uses:
    conn.execute(f"""
        MATCH (proj:Project {{name: '{project}'}}), (t:Technology {{name: '{tech}'}})
        CREATE (proj)-[:USES]->(t)
    """)

print("✓ Зв'язки додано")

# ============================================================
# КРОК 5: Перші запити (queries)
# ============================================================

print("\n" + "="*50)
print("ЗАПИТИ ДО ГРАФУ")
print("="*50)

# --- Запит 1: Всі технології проекту AgentRa ---
print("\n📌 Запит 1: Які технології використовує AgentRa?")
result = conn.execute("""
    MATCH (proj:Project {name: 'AgentRa'})-[:USES]->(t:Technology)
    RETURN t.name AS технологія, t.category AS категорія
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} ({row[1]})")

# --- Запит 2: Всі проекти де є Claude API ---
print("\n📌 Запит 2: В яких проектах використовується Claude API?")
result = conn.execute("""
    MATCH (proj:Project)-[:USES]->(t:Technology {name: 'Claude API'})
    RETURN proj.name AS проект, proj.status AS статус
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} ({row[1]})")

# --- Запит 3: Всі проекти Євгенія ---
print("\n📌 Запит 3: Над якими проектами працює Євгеній?")
result = conn.execute("""
    MATCH (p:Person {name: 'Євгеній'})-[r:WORKS_ON]->(proj:Project)
    RETURN proj.name AS проект, r.since AS рік_початку
    ORDER BY r.since
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} (з {row[1]})")

# --- Запит 4: 2 рівні — технології через людину ---
# Це вже ПОТУЖНО: знайти всі технології через всі проекти однієї людини
print("\n📌 Запит 4: Всі технології, з якими працює Євгеній (через проекти):")
result = conn.execute("""
    MATCH (p:Person {name: 'Євгеній'})-[:WORKS_ON]->(proj:Project)-[:USES]->(t:Technology)
    RETURN t.name AS технологія, t.category AS категорія, proj.name AS через_проект
    ORDER BY t.category
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} ({row[1]}) — через {row[2]}")

# --- Запит 5: Проекти що мають спільні технології ---
print("\n📌 Запит 5: Які проекти мають спільні технології?")
result = conn.execute("""
    MATCH (p1:Project)-[:USES]->(t:Technology)<-[:USES]-(p2:Project)
    WHERE p1.name < p2.name
    RETURN p1.name AS проект_1, p2.name AS проект_2, t.name AS спільна_технологія
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} + {row[1]} → спільна: {row[2]}")

print("\n✓ Тиждень 1 завершено!")
print("="*50)
print("\n📌 Запит 6: Яка технологія у найбільшій кількості проектів?")
result = conn.execute("""
    MATCH (proj:Project)-[:USES]->(t:Technology)
    RETURN t.name AS технологія, COUNT(proj) AS кількість
    ORDER BY кількість DESC
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]}: {row[1]} проект(и)")
print("\n" + "="*50)
print("ПРАКТИЧНІ ЗАВДАННЯ")
print("="*50)

# --- Завдання 1: Всі люди і їх проекти ---
print("\n📌 Завдання 1: Всі люди і їх проекти")
result = conn.execute("""
    MATCH (p:Person)-[:WORKS_ON]->(proj:Project)
    RETURN p.name AS людина, proj.name AS проект
    ORDER BY p.name
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} → {row[1]}")

# --- Завдання 2: Технології яких немає в AgentRa ---
print("\n📌 Завдання 2: Технології яких немає в AgentRa")
result = conn.execute("""
    MATCH (proj:Project)-[:USES]->(t:Technology)
    WHERE proj.name <> 'AgentRa'
    AND NOT EXISTS {
        MATCH (a:Project {name: 'AgentRa'})-[:USES]->(t)
    }
    RETURN DISTINCT t.name AS технологія
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]}")

# --- Завдання 3: Кількість технологій у кожному проекті ---
print("\n📌 Завдання 3: Кількість технологій у кожному проекті")
result = conn.execute("""
    MATCH (proj:Project)-[:USES]->(t:Technology)
    RETURN proj.name AS проект, COUNT(t) AS кількість_технологій
    ORDER BY кількість_технологій DESC
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]}: {row[1]} технологій")

# --- Завдання 4: Хто працює з однаковими технологіями ---
print("\n📌 Завдання 4: Хто працює з однаковими технологіями?")
result = conn.execute("""
    MATCH (p1:Person)-[:WORKS_ON]->(proj1:Project)-[:USES]->(t:Technology)
          <-[:USES]-(proj2:Project)<-[:WORKS_ON]-(p2:Person)
    WHERE p1.name < p2.name
    RETURN DISTINCT p1.name AS людина_1, p2.name AS людина_2, t.name AS спільна_технологія
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} + {row[1]} → через: {row[2]}")

print("\n✓ Всі завдання виконано!")
print("Наступний крок: тиждень 2 — мова Cypher і концепти знань")
