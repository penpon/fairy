import sqlite3


def get_user_data(user_id):
    """
    Retrieve user data from the database by user ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        List of tuples containing user data, or None if an error occurs

    Raises:
        sqlite3.Error: If a database error occurs
    """
    try:
        # Use context manager to ensure proper resource cleanup
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()

            # Use parameterized query to prevent SQL injection
            query = "SELECT * FROM users WHERE id = ?"
            cursor.execute(query, (user_id,))

            result = cursor.fetchall()
            return result
    except sqlite3.Error as e:
        # Log the error and re-raise for proper handling by caller
        print(f"Database error: {e}")
        raise
