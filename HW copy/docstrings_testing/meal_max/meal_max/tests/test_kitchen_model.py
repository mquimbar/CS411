from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats,
    clear_meals
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the catalog."""

    # Call the function to create a new meal
    create_meal(meal="Meal Name", cuisine="Cuisine Type", price=20, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name", "Cuisine Type", 20, "MED")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate meal name (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meal.meal, meal.cuisine, meal.price")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists"):
        create_meal(meal="Meal Name", cuisine="Cuisine Type", price=20, difficulty="MED")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative price)"""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -20. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Cuisine Type", price=-20, difficulty="MED")
    
    # Attempt to create a meal with a non-integer price
    with pytest.raises(ValueError, match="Invalid price: invalid. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Cuisine Type", price="invalid", difficulty="MED")

def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty (e.g., not in ['LOW', 'MED', 'HIGH'])."""

    # Attempt to create a meal with difficulty that is not in ['LOW', 'MED', 'HIGH']
    with pytest.raises(ValueError, match="Invalid difficulty level: YES. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Meal Name", cuisine="Cuisine Type", price=20, difficulty="YES")
    
def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the databse by meal ID."""

    # Simulate that the song exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_song function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the song exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a song that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)

def test_clear_meals(mock_cursor, mocker):
    """Test clearing all meals from the database."""
    
    mock_create_table_script = """
    DROP TABLE IF EXISTS meals;
    CREATE TABLE meals (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        cuisine TEXT NOT NULL,
        price REAL NOT NULL,
        difficulty TEXT NOT NULL,
        deleted BOOLEAN DEFAULT FALSE,
        battles INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0
    );
    """
    
    mock_file = mocker.mock_open(read_data=mock_create_table_script)
    mocker.patch("builtins.open", mock_file)
    
    clear_meals()

    mock_cursor.executescript.assert_called_once_with(mock_create_table_script)
    assert mock_cursor.connection.commit.call_count == 0


######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor): #*****
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Type", 20, "MED", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Type", 20, "MED")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_id_bad_id(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the song is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists (meal = "Meal Name", cuisine = "Cuisine Type", price = 20)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Type", 20, "MED", False)

    # Call the function and check the result
    result = get_meal_by_name("Meal Name")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Type", 20, "MED")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name",) 
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_leaderboard(mock_cursor):
    """Test retrieving leaderboard for meals that are not marked as deleted."""

    # Simulate that there are multiple meals in the leaderboard
    mock_cursor.fetchall.return_value = [
        (1, "Meal A", "Cuisine A", 20, "LOW", 100, 50, 0.5, False),
        (2, "Meal B", "Cuisine B", 21, "MED", 100, 30, 0.3, False),
        (3, "Meal C", "Cuisine C", 22, "HIGH", 100, 20, 0.2, False)
    ]

    # Call the get_leaderboard function
    meals = get_leaderboard()

    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 20, "difficulty": "LOW", "battles": 100, "wins": 50, "win_pct": 50},
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 21, "difficulty": "MED", "battles": 100, "wins": 30, "win_pct": 30},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 22, "difficulty": "HIGH", "battles": 100, "wins": 20, "win_pct": 20}
    ] 

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals
        WHERE deleted = false
        AND battles > 0
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_ordered_by_wins(mock_cursor):
    """Test retrieving all meals ordered by wins."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "Meal B", "Cuisine B", 21, "MED", 100, 50, 0.5),
        (1, "Meal A", "Cuisine A", 20, "LOW", 100, 30, 0.3),
        (3, "Meal C", "Cuisine C", 22, "HIGH", 100, 20, 0.2)
    ] 

    # Call the get_leaderboard function with sort_by = "wins"
    meals = get_leaderboard(sort_by="wins")

    # Ensure the results are sorted by wins
    expected_result = [
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 21, "difficulty": "MED", "battles": 100, "wins": 50, "win_pct": 50},
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 20, "difficulty": "LOW", "battles": 100, "wins": 30, "win_pct": 30},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 22, "difficulty": "HIGH", "battles": 100, "wins": 20, "win_pct": 20}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals
        WHERE deleted = false
        AND battles > 0
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_ordered_by_win_pct(mock_cursor):
    """Test retrieving all meals ordered by win_pct."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "Meal B", "Cuisine B", 21, "MED", 100, 50, 0.5),
        (1, "Meal A", "Cuisine A", 20, "LOW", 100, 30, 0.3),
        (3, "Meal C", "Cuisine C", 22, "HIGH", 100, 20, 0.2)
    ]

    # Call the get_leaderboard function with sort_by = "win_pct"
    meals = get_leaderboard(sort_by="win_pct")

    # Ensure the results are sorted by win_pct
    expected_result = [
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 21, "difficulty": "MED", "battles": 100, "wins": 50, "win_pct": 50},
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 20, "difficulty": "LOW", "battles": 100, "wins": 30, "win_pct": 30},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 22, "difficulty": "HIGH", "battles": 100, "wins": 20, "win_pct": 20}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals
        WHERE deleted = false
        AND battles > 0
        ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_ordered_by_bad_sort(mock_cursor):
    """Test retrieving all meals ordered by an invalid input."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "Meal B", "Cuisine B", 21, "MED", 100, 50, 50),
        (1, "Meal A", "Cuisine A", 20, "LOW", 100, 30, 30),
        (3, "Meal C", "Cuisine C", 22, "HIGH", 100, 20, 20)
    ]

    # Expect a ValueError when the sort_by is not "wins" or "win_pct"
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        meals = get_leaderboard(sort_by="invalid")

def test_update_meal_stats_win(mock_cursor):
    """Test updating the meal stats of a meal with a win."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_play_count function with a sample song ID
    meal_id = 1
    update_meal_stats(meal_id, "win")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (song ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_loss(mock_cursor):
    """Test updating the meal stats of a meal with a loss."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_play_count function with a sample song ID
    meal_id = 1
    update_meal_stats(meal_id, "loss")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (song ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when trying to update meal stats for a deleted meal."""

    # Simulate that the song exists but is marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted song
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")

    # Ensure that no SQL query for updating play count was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

def test_update_meal_stats_bad_id(mock_cursor):
    """Test error when trying to update meal stats for a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent song
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, "win")

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test error when trying to update meal stats with an invalid result."""

    # Simulate that the song exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    meal_id = 1

    # Expect a ValueError when attempting to update the meal stats with an invalid result
    with pytest.raises(ValueError, match="Invalid result: yes. Expected 'win' or 'loss'."):
        update_meal_stats(meal_id, "yes")