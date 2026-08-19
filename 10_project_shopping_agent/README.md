# 🛒 AI Shopping Assistant

An AI-powered shopping assistant built with LangChain, Groq LLMs, and Streamlit. Search for products by text or image, check ratings, and place orders — all through a conversational interface.

## Features

- **Text search** — Find products by name, category, price, or organic preference
- **Image search** — Upload a product photo and find similar items in the store
- **Ratings** — Automatically fetches average customer ratings for each result
- **Checkout** — Place orders directly from the chat

## Project Structure

```
10_project_shopping_agent/
├── app.py              # Streamlit UI
├── shopping_agent.py   # LangChain agent + tools
├── reviews_api.py      # SQLite reviews helper
├── store.db            # SQLite database (products, reviews, orders)
└── resources/          # Sample product images
```

## Requirements

```
streamlit
langchain
langchain-groq
python-dotenv
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Add your Groq API key to `.env`:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Usage

- **Chat**: Type a request like `I want organic honey under $15 with 4+ rating`
- **Image search**: Upload a product image in the sidebar and click "Find similar products"
- **Order**: Confirm when prompted to place an order

## Agent Tools

| Tool | Description |
|------|-------------|
| `search_products` | Query products by keyword, price, and organic filter |
| `get_rating` | Fetch average rating and review count for a product |
| `desc_product_image` | Analyze an uploaded image to extract search attributes |
| `checkout` | Place an order for a product by ID |
