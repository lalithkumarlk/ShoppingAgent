import os
import json
import sqlite3
from typing import Optional
from reviews_api import get_product_rating
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain.agents import create_agent
import base64

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

model = "openai/gpt-oss-120b"
# The model name "qwen/qwen3-32b" appears to be valid for ChatGroq, but you should verify it against the official ChatGroq documentation or API to ensure it's a supported model name and version.
llm = ChatGroq(model=model, temperature=0)
vision_llm = ChatGroq(model="qwen/qwen3.6-27b", temperature=0)


@tool
def search_products(
    query: str,
    max_price: Optional[float] = None,
    is_organic: Optional[str] = None,
) -> str:
    """
    Searches for products.

    Args:
        query : The search query to match against product names and descriptions.
        max_price : The maximum price of the products to return. If None, no price filtering is applied.
        is_organic: if Organic then "true" else "false", or null for no filter

    """
    try:
        # convert string to bool
        if isinstance(is_organic, str):
            if is_organic.lower() == "true":
                is_organic = True
            elif is_organic.lower() == "false":
                is_organic = False
            else:
                is_organic = None
        elif is_organic is None:
            is_organic = None
        else:
            is_organic = None

        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Prepare the base SQL query
        sql_query = "SELECT id, name, category, price, description, is_organic  FROM products WHERE 1=1"
        params = []

        if query:
            sql_query += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query])

        # Add price filtering if max_price is provided
        if max_price is not None:
            sql_query += " AND price <= ?"
            params.append(max_price)

        # Add organic filtering if is_organic is True

        if is_organic == True:
            sql_query += " AND is_organic = 1"
        elif is_organic == False:
            sql_query += " AND is_organic = 0"
        # is_organic is None means no filter

        # print(sql_query, params)
        # Execute the query with parameters
        cursor.execute(sql_query, params)
        results = cursor.fetchall()

        # print("Results:", results)
        # Convert results to a list of dictionaries
        products = [
            {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "price": row[3],
                "description": row[4],
                "is_organic": bool(row[5]),
            }
            for row in results
        ]
        return products
    # json.dumps(products)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

    finally:
        # Close the database connection
        if conn:
            conn.close()


@tool
def desc_product_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.
    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """

    with open(image_path, "rb") as f:
        # convert image to base64
        image_data = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{image_data}"},
            },
            {
                "type": "text",
                "text": (
                    "Look at this product image and extract its key attributes. "
                    "Return ONLY a JSON object with these fields:\n"
                    "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                    "- search_query: a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                    '- is_organic: "true" if the label says organic, "false" if not, null if unclear\n'
                    "- description: one sentence describing the product"
                ),
            },
        ]
    )
    response = vision_llm.invoke([message])
    return response.content


@tool
def get_rating(product_id: int) -> str:
    """
    get the average customer rating & total review count for a product by its id.
    Return Json object with: product_id, average_rating, review_count
    """
    result = get_product_rating(product_id)
    return json.dumps(result)


@tool
def checkout(product_id: int) -> str:
    """
    Checkout a product by its id.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute a query to fetch the product details
        cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if product:
            name, price = product
            print(f"Checkout successful for {name} with price ${price}.")
            # insert into orders table
            cursor.execute(
                "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
                (product_id, name, price),
            )
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return f"Order placed successfully with order_id: {order_id}"
        else:
            return "Product not found."

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error occurred while processing checkout."

    finally:
        # Close the database connection
        if conn:
            conn.close()


SYSTEM_PROMPT = """
You are a helpful shopping assistant.

IMAGE SEARCH:
- When the user provides an image path, call desc_product_image with the path.
- Use the returned search_query and is_organic to call search_products.
- Then continue with the BROWSING flow.

BROWSING:
- For product requests, call search_products, then get_rating for each result.
- Apply price, organic, and minimum-rating filters.
- Display results as:

#1. <name> (ID:<id>) — $<price> ★<rating> — <organic/non-organic>

- Always include product IDs and a blank line between products.
- If only one product qualifies, ask:
  "Would you like to order it? Just say yes or give me the number."
- Never call checkout while browsing.

ORDERING:
- Only call checkout after explicit user confirmation.
- Use the product ID from your previous response.
- Never guess a product ID.
- After checkout, confirm the order.
"""
agent = create_agent(
    llm,
    [search_products, get_rating, desc_product_image, checkout],
    system_prompt=SYSTEM_PROMPT,
)

if __name__ == "__main__":
    messages = []

    while True:
        query = input("You: ")

        if query.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        messages.append(HumanMessage(content=query))

        response = agent.invoke({"messages": messages})

        messages = response["messages"]

        print("Assistant:", messages[-1].content)
