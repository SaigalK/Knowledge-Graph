"""
ТИЖДЕНЬ 5: MCP сервер для Knowledge Graph
Claude Desktop зможе питати твій Knowledge Graph прямо з чату!

MCP (Model Context Protocol) — це протокол від Anthropic.
Він дозволяє Claude підключатись до зовнішніх інструментів (твій код).
Claude викликає функції твого сервера — як плагіни для ChatGPT, але потужніше.

Цей файл ТРЕБА запускати через .venv/bin/python (Python 3.11), а не через python3
"""
import sys
import os

# Додаємо папку проекту до шляху щоб знайти config.py
sys.path.insert(0, "/Users/mac/Documents/Lucky")

import kuzu
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
import mcp.server.stdio
import mcp.types as types
from openai import OpenAI
from config import OPENROUTER_API_KEY, DEFAULT_MODEL

# ============================================================
# ПІДКЛЮЧЕННЯ ДО БАЗ ДАНИХ
# ============================================================

# Knowledge Graph з тижня 3
db = kuzu.Database("/Users/mac/Documents/Lucky/knowledge_graph")
conn = kuzu.Connection(db)

# OpenRouter для LLM відповідей
llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ============================================================
# ФУНКЦІЇ ПОШУКУ (ті самі що в week4, але тут вони потрібні серверу)
# ============================================================

def знайди_контекст(запит: str) -> str:
    """Шукає у Knowledge Graph концепти пов'язані із запитом."""
    слова = запит.lower().split()
    знайдено = {}

    for слово in слова:
        if len(слово) < 3:
            continue
        if "'" in слово or "'" in слово:
            continue

        safe = слово.replace("'", "''")
        result = conn.execute(f"""
            MATCH (d:Document)-[:CONTAINS]->(c:Concept)
            WHERE LOWER(c.name) CONTAINS '{safe}'
            RETURN d.title AS документ, c.name AS концепт
            ORDER BY d.title
        """)
        while result.has_next():
            row = result.get_next()
            doc, concept = row[0], row[1]
            if doc not in знайдено:
                знайдено[doc] = []
            if concept not in знайдено[doc]:
                знайдено[doc].append(concept)

    if not знайдено:
        return ""

    рядки = ["КОНТЕКСТ З БАЗИ ЗНАНЬ:"]
    for документ, концепти in знайдено.items():
        рядки.append(f"\nДокумент: {документ}")
        рядки.append(f"Теми: {', '.join(концепти[:8])}")
    return "\n".join(рядки)


def запитай_llm(питання: str, контекст: str) -> str:
    """Надсилає питання до LLM з контекстом з графу."""
    if контекст:
        системний = f"""Ти — асистент який відповідає ТІЛЬКИ на основі наданого контексту.
Якщо відповідь не можна знайти у контексті — скажи "У базі знань немає інформації про це".
Не вигадуй факти яких немає у контексті.

{контекст}"""
    else:
        системний = "Для цього питання у базі знань немає інформації. Відповідай чесно."

    response = llm_client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": системний},
            {"role": "user", "content": питання}
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content

# ============================================================
# MCP СЕРВЕР
# ============================================================
# Server("назва") — створює MCP сервер з іменем
# @server.list_tools() — каже Клоду: "ось список інструментів що я пропоную"
# @server.call_tool() — обробляє виклик конкретного інструменту

server = Server("kuzu-knowledge-graph")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    Список інструментів що Claude побачить у чаті.
    Кожен інструмент — це функція яку Claude може викликати.
    """
    return [
        types.Tool(
            name="search_graph",
            description="Шукає у Knowledge Graph документи та концепти за ключовим словом. "
                        "Використовуй коли потрібно знайти що є в базі знань.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Ключове слово або фраза для пошуку"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="ask_knowledge_base",
            description="Задає питання до Knowledge Graph і отримує відповідь від LLM "
                        "на основі збережених документів. Anti-hallucination RAG.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Питання до бази знань"
                    }
                },
                "required": ["question"]
            }
        ),
        types.Tool(
            name="list_documents",
            description="Показує всі документи у Knowledge Graph з кількістю концептів.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_concepts",
            description="Показує всі концепти з конкретного документу.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document": {
                        "type": "string",
                        "description": "Назва документу"
                    }
                },
                "required": ["document"]
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    Обробляє виклик інструменту від Claude.
    name — назва інструменту (наприклад "search_graph")
    arguments — параметри які надіслав Claude (наприклад {"query": "RAG"})
    """

    if name == "search_graph":
        запит = arguments.get("query", "")
        контекст = знайди_контекст(запит)

        if контекст:
            відповідь = контекст
        else:
            відповідь = f"За запитом '{запит}' нічого не знайдено у Knowledge Graph."

        return [types.TextContent(type="text", text=відповідь)]

    elif name == "ask_knowledge_base":
        питання = arguments.get("question", "")
        контекст = знайди_контекст(питання)
        відповідь = запитай_llm(питання, контекст)

        повна = f"Питання: {питання}\n\n{відповідь}"
        if контекст:
            повна += f"\n\n---\n{контекст}"

        return [types.TextContent(type="text", text=повна)]

    elif name == "list_documents":
        result = conn.execute("""
            MATCH (d:Document)-[:CONTAINS]->(c:Concept)
            RETURN d.title AS документ, COUNT(c) AS концептів
            ORDER BY концептів DESC
        """)
        рядки = ["Документи у Knowledge Graph:\n"]
        while result.has_next():
            row = result.get_next()
            рядки.append(f"• {row[0]} — {row[1]} концептів")
        return [types.TextContent(type="text", text="\n".join(рядки))]

    elif name == "get_concepts":
        doc = arguments.get("document", "")
        safe_doc = doc.replace("'", "''")
        result = conn.execute(f"""
            MATCH (d:Document {{title: '{safe_doc}'}})-[:CONTAINS]->(c:Concept)
            RETURN c.name
            ORDER BY c.name
        """)
        концепти = []
        while result.has_next():
            концепти.append(result.get_next()[0])

        if концепти:
            текст = f"Концепти документу '{doc}':\n\n" + "\n".join(f"• {к}" for к in концепти)
        else:
            текст = f"Документ '{doc}' не знайдено або він порожній."

        return [types.TextContent(type="text", text=текст)]

    else:
        return [types.TextContent(type="text", text=f"Невідомий інструмент: {name}")]


# ============================================================
# ЗАПУСК СЕРВЕРА
# ============================================================
# stdio = стандартний ввід/вивід
# Claude Desktop запускає цей файл як підпроцес і спілкується через stdin/stdout
# Тому сервер не відкриває порт — він просто читає команди з термінала

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kuzu-knowledge-graph",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(tools_changed=False),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
