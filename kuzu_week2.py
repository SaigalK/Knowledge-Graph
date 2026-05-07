"""
ТИЖДЕНЬ 2: Cypher глибше + Concept nodes
Нові команди: SET, WHERE, нові типи вузлів
"""
import kuzu

# Підключаємось до тієї самої бази що створили на тижні 1
db = kuzu.Database("./my_first_graph")
conn = kuzu.Connection(db)

print("✓ Підключились до бази")

# ============================================================
# УРОК 1: Команда SET — оновити дані
# ============================================================
# SET змінює значення поля у вузлі що вже існує
# Синтаксис: MATCH (вузол) SET вузол.поле = нове_значення

print("\n" + "="*50)
print("УРОК 1: Команда SET")
print("="*50)

# Подивимось що зараз у проекту AgentRa
print("\nДо змін:")
result = conn.execute("MATCH (p:Project {name: 'AgentRa'}) RETURN p.name, p.status")
row = result.get_next()
print(f"   {row[0]} → статус: {row[1]}")

# Оновлюємо статус AgentRa
# MATCH знаходить вузол, SET змінює поле
conn.execute("""
    MATCH (p:Project {name: 'AgentRa'})
    SET p.status = 'production'
""")

# Перевіряємо що змінилось
print("Після SET:")
result = conn.execute("MATCH (p:Project {name: 'AgentRa'}) RETURN p.name, p.status")
row = result.get_next()
print(f"   {row[0]} → статус: {row[1]}")

# SET може оновлювати кілька полів одразу через кому
conn.execute("""
    MATCH (p:Person {name: 'Євгеній'})
    SET p.role = 'Founder & Director'
""")

print("\nОновили роль Євгенія:")
result = conn.execute("MATCH (p:Person {name: 'Євгеній'}) RETURN p.name, p.role")
row = result.get_next()
print(f"   {row[0]} → роль: {row[1]}")

# ============================================================
# УРОК 2: WHERE з різними умовами
# ============================================================
# WHERE фільтрує результати — як у SQL
# Можна використовувати: =, <>, <, >, <=, >=, AND, OR, NOT

print("\n" + "="*50)
print("УРОК 2: WHERE — фільтри")
print("="*50)

# Знайти тільки активні проекти
print("\nТільки активні проекти (status = 'active'):")
result = conn.execute("""
    MATCH (p:Project)
    WHERE p.status = 'active'
    RETURN p.name, p.status
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} ({row[1]})")

# Знайти технології категорії backend або LLM
print("\nТехнології категорії 'backend' або 'LLM':")
result = conn.execute("""
    MATCH (t:Technology)
    WHERE t.category = 'backend' OR t.category = 'LLM'
    RETURN t.name, t.category
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} ({row[1]})")

# Знайти проекти де Євгеній починав ДО 2025
print("\nПроекти де Євгеній починав ДО 2025 року:")
result = conn.execute("""
    MATCH (p:Person {name: 'Євгеній'})-[r:WORKS_ON]->(proj:Project)
    WHERE r.since < 2025
    RETURN proj.name, r.since
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} (з {row[1]})")

# ============================================================
# УРОК 3: Новий тип вузла — Concept
# ============================================================
# Concept (концепт) — це ключове поняття або тема
# Наприклад: 'RAG', 'LLM', 'автоматизація', 'графова БД'
#
# НАВІЩО ДЛЯ ANTI-HALLUCINATION:
# Коли LLM відповідає — вона може вигадати зв'язок між поняттями.
# Якщо в графі є явні зв'язки Project → Concept → Concept,
# LLM отримує перевірену карту знань і не може вигадати те,
# чого немає у графі.

print("\n" + "="*50)
print("УРОК 3: Concept nodes — серце Knowledge Graph")
print("="*50)

# Створюємо новий тип вузла Concept
conn.execute("""
    CREATE NODE TABLE IF NOT EXISTS Concept(
        name STRING,
        definition STRING,
        PRIMARY KEY(name)
    )
""")

# Створюємо тип зв'язку: Project → Concept (проект стосується концепту)
conn.execute("CREATE REL TABLE IF NOT EXISTS ABOUT(FROM Project TO Concept)")

# Створюємо тип зв'язку: Concept → Concept (один концепт пов'язаний з іншим)
conn.execute("CREATE REL TABLE IF NOT EXISTS RELATED_TO(FROM Concept TO Concept, strength FLOAT)")

print("✓ Нові таблиці створено: Concept, ABOUT, RELATED_TO")

# Додаємо концепти — MERGE щоб не дублювати
concepts = [
    ("RAG", "Retrieval-Augmented Generation — пошук інформації перед генерацією відповіді"),
    ("LLM", "Large Language Model — велика мовна модель типу Claude або GPT"),
    ("Knowledge Graph", "Граф знань — структурована мережа концептів"),
    ("Vector DB", "Векторна база даних для пошуку за схожістю"),
    ("Автоматизація", "Виконання задач без участі людини за допомогою програм"),
    ("Telegram Bot", "Чат-бот у месенджері Telegram"),
    ("PDF генерація", "Автоматичне створення PDF файлів через код"),
    ("Веб розробка", "Створення сайтів та вебзастосунків"),
    ("Будівництво", "Проектування та зведення будівель і споруд"),
]

for name, definition in concepts:
    # Замінюємо апостроф на два апострофи — так Kuzu розуміє що це частина тексту
    safe_name = name.replace("'", "''")
    safe_def = definition.replace("'", "''")
    conn.execute(f"""
        MERGE (:Concept {{name: '{safe_name}', definition: '{safe_def}'}})
    """)

print(f"✓ Додано {len(concepts)} концептів")

# ============================================================
# УРОК 4: Зв'язуємо проекти з концептами
# ============================================================

print("\n" + "="*50)
print("УРОК 4: Зв'язуємо проекти з концептами")
print("="*50)

# Спочатку видаляємо старі ABOUT зв'язки (якщо запускаємо повторно)
conn.execute("MATCH ()-[r:ABOUT]->() DELETE r")
conn.execute("MATCH ()-[r:RELATED_TO]->() DELETE r")

# Кожен проект ABOUT певні концепти
project_concepts = [
    ("AgentRa",           "LLM"),
    ("AgentRa",           "Автоматизація"),
    ("AgentRa",           "Telegram Bot"),
    ("RAG Telegram Bot",  "RAG"),
    ("RAG Telegram Bot",  "LLM"),
    ("RAG Telegram Bot",  "Vector DB"),
    ("RAG Telegram Bot",  "Telegram Bot"),
    ("KDP Coloring Book", "Автоматизація"),
    ("KDP Coloring Book", "PDF генерація"),
    ("САНЕКО сайт",       "Будівництво"),
    ("САНЕКО сайт", "Веб розробка"),
    ("САНЕКО сайт",       "Автоматизація"),
]

for project, concept in project_concepts:
    conn.execute(f"""
        MATCH (proj:Project {{name: '{project}'}}),
              (c:Concept {{name: '{concept}'}})
        CREATE (proj)-[:ABOUT]->(c)
    """)

print(f"✓ Додано {len(project_concepts)} зв'язків проект→концепт")

# Концепти пов'язані між собою
concept_relations = [
    ("RAG",           "LLM",           0.9),
    ("RAG",           "Vector DB",     0.8),
    ("LLM",           "Knowledge Graph", 0.7),
    ("Knowledge Graph", "Vector DB",   0.6),
    ("Автоматизація", "Telegram Bot",  0.5),
]

for c1, c2, strength in concept_relations:
    conn.execute(f"""
        MATCH (a:Concept {{name: '{c1}'}}),
              (b:Concept {{name: '{c2}'}})
        CREATE (a)-[:RELATED_TO {{strength: {strength}}}]->(b)
    """)

print(f"✓ Додано {len(concept_relations)} зв'язків між концептами")

# ============================================================
# УРОК 5: Запити на 3 рівні — сила Knowledge Graph
# ============================================================

print("\n" + "="*50)
print("УРОК 5: Запити на 3 рівні глибини")
print("="*50)

# Рівень 1: Прямий — концепти проекту
print("\n📌 Рівень 1: Концепти проекту AgentRa")
result = conn.execute("""
    MATCH (proj:Project {name: 'AgentRa'})-[:ABOUT]->(c:Concept)
    RETURN c.name AS концепт
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]}")

# Рівень 2: Через концепти — пов'язані концепти
print("\n📌 Рівень 2: Суміжні концепти для AgentRa (через RELATED_TO)")
result = conn.execute("""
    MATCH (proj:Project {name: 'AgentRa'})-[:ABOUT]->(c:Concept)-[:RELATED_TO]->(related:Concept)
    RETURN c.name AS концепт, related.name AS пов_язаний
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} → {row[1]}")

# Рівень 3: Через людину → проекти → концепти → суміжні
# Це і є Knowledge Graph для anti-hallucination:
# LLM отримує не просто текст, а СТРУКТУРОВАНИЙ КОНТЕКСТ
print("\n📌 Рівень 3: Весь контекст знань Євгенія (людина→проект→концепт→суміжний)")
result = conn.execute("""
    MATCH (p:Person {name: 'Євгеній'})
          -[:WORKS_ON]->(proj:Project)
          -[:ABOUT]->(c:Concept)
          -[:RELATED_TO]->(related:Concept)
    RETURN proj.name AS проект, c.name AS концепт, related.name AS суміжний
    ORDER BY proj.name
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]} → {row[1]} → {row[2]}")

# ============================================================
# УРОК 6: Пошук визначення концепту
# ============================================================
# Це прообраз того що робитиме RAG:
# отримати запит → знайти концепт у графі → повернути визначення

print("\n" + "="*50)
print("УРОК 6: Пошук визначення — прообраз RAG")
print("="*50)

def знайди_концепт(назва):
    """
    Функція яка шукає концепт у графі і повертає:
    - визначення
    - в яких проектах зустрічається
    - суміжні концепти
    """
    result = conn.execute(f"""
        MATCH (c:Concept {{name: '{назва}'}})
        RETURN c.name, c.definition
    """)

    if not result.has_next():
        return f"Концепт '{назва}' не знайдено у базі знань"

    row = result.get_next()
    назва_знайдена, визначення = row[0], row[1]

    # Знайти проекти
    result2 = conn.execute(f"""
        MATCH (proj:Project)-[:ABOUT]->(c:Concept {{name: '{назва}'}})
        RETURN proj.name
    """)
    проекти = []
    while result2.has_next():
        проекти.append(result2.get_next()[0])

    # Знайти суміжні концепти
    result3 = conn.execute(f"""
        MATCH (c:Concept {{name: '{назва}'}})-[r:RELATED_TO]->(related:Concept)
        RETURN related.name, r.strength
        ORDER BY r.strength DESC
    """)
    суміжні = []
    while result3.has_next():
        r = result3.get_next()
        суміжні.append(f"{r[0]} (схожість: {r[1]})")

    відповідь = f"""
Концепт: {назва_знайдена}
Визначення: {визначення}
Зустрічається в проектах: {', '.join(проекти) if проекти else 'жодного'}
Суміжні концепти: {', '.join(суміжні) if суміжні else 'жодного'}
    """
    return відповідь.strip()

# Тестуємо функцію
print("\n" + знайди_концепт("RAG"))
print("\n" + знайди_концепт("LLM"))
print("\n" + знайди_концепт("Блокчейн"))  # якого немає в базі

print("\n✓ Тиждень 2 завершено!")
print("="*50)
print("\n📌 Завдання 2: Найпопулярніші концепти")
result = conn.execute("""
    MATCH (proj:Project)-[:ABOUT]->(c:Concept)
    RETURN c.name AS концепт, COUNT(proj) AS кількість_проектів
    ORDER BY кількість_проектів DESC
""")
while result.has_next():
    row = result.get_next()
    print(f"   {row[0]}: {row[1]} проект(и)")

print("\n📌 Завдання 3: Довідник всіх концептів")
result = conn.execute("MATCH (c:Concept) RETURN c.name ORDER BY c.name")
всі_концепти = []
while result.has_next():
    всі_концепти.append(result.get_next()[0])

print(f"Всього концептів у базі: {len(всі_концепти)}")
for концепт in всі_концепти:
    print("\n---")
    print(знайди_концепт(концепт))
print("Наступний крок: тиждень 3 — Knowledge Graph з реальних документів")
