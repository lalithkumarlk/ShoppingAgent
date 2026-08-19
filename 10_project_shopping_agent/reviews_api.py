import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")


def get_product_rating(product_id: int) -> dict:
    """
    Fetches reviews for a given product from the SQLite database.

    Args:
        product_id (int): The ID of the product for which to fetch reviews.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute a query to fetch reviews for the specified product_id
        cursor.execute(
            "SELECT AVG(rating) as average_rating, count(*) as review_count FROM reviews WHERE product_id = ?",
            (product_id,),
        )
        results = cursor.fetchone()

        if results:
            average_rating, review_count = results
            return {
                "product_id": product_id,
                "average_rating": average_rating if average_rating is not None else 0,
                "review_count": review_count,
            }

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

    finally:
        # Close the database connection
        if conn:
            conn.close()


def get_ratings_for_products(product_ids: list) -> dict:
    """
    Fetches reviews for a list of products from the SQLite database.

    Args:
        product_ids (list): A list of product IDs for which to fetch reviews.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Prepare a query to fetch reviews for the specified product_ids
        placeholders = ", ".join(["?"] * len(product_ids))
        query = f"SELECT product_id, AVG(rating) as average_rating, count(*) as review_count FROM reviews WHERE product_id IN ({placeholders}) GROUP BY product_id"
        cursor.execute(query, product_ids)
        results = cursor.fetchall()

        ratings_dict = {}
        for row in results:
            product_id, average_rating, review_count = row
            ratings_dict[product_id] = {
                "average_rating": average_rating if average_rating is not None else 0,
                "review_count": review_count,
            }

        return ratings_dict

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {}

    finally:
        # Close the database connection
        if conn:
            conn.close()


if __name__ == "__main__":
    # Example usage
    product_id = 1
    print(get_product_rating(product_id))

    product_ids = [1, 2, 3]
    print(get_ratings_for_products(product_ids))
