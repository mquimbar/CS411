import pytest
from unittest.mock import Mock
from unittest.mock import patch


from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal
from meal_max.utils.random_utils import get_random


# Fixtures

@pytest.fixture
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture
def sample_meal1():
    """Fixture providing a sample meal as a combatant."""
    return Meal(id=1, meal="Spaghetti", cuisine="Italian", price=10.0, difficulty="MED")

@pytest.fixture
def sample_meal2():
    """Fixture providing another sample meal as a combatant."""
    return Meal(id=2, meal="Sushi", cuisine="Japanese", price=15.0, difficulty="HIGH")

@pytest.fixture
def mock_update_meal_stats(mocker):
    """Mock the update_meal_stats function for testing purposes."""
    return mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

@pytest.fixture
def mock_get_random(mocker):
    """Mock the get_random function to control randomness in tests."""
    return mocker.patch("meal_max.utils.random_utils.get_random", return_value=0.5)

# Test Cases

def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a combatant to the battle."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 1
    assert battle_model.get_combatants()[0].meal == "Spaghetti"

def test_prep_duplicate_combatant(battle_model, sample_meal1):
    """Test error when adding more than two combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Combatant list is full"):
        battle_model.prep_combatant(sample_meal1)

def test_battle_insufficient_combatants(battle_model, sample_meal1):
    """Test that battle raises error if fewer than two combatants are prepped."""
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle"):
        battle_model.battle()

def test_battle_winner(battle_model, sample_meal1, sample_meal2, mock_update_meal_stats, mock_get_random, mocker):
    """Test battle outcome and stats update."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Mock scores to control the winner outcome
    with mocker.patch.object(battle_model, "get_battle_score", side_effect=[80, 60]):
        winner = battle_model.battle()
        assert winner == sample_meal1.meal  # Expected winner

        # Verify that update_meal_stats was called correctly
        mock_update_meal_stats.assert_any_call(sample_meal1.id, 'win')
        mock_update_meal_stats.assert_any_call(sample_meal2.id, 'loss')

def test_clear_combatants(battle_model, sample_meal1, sample_meal2):
    """Test clearing the list of combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    battle_model.clear_combatants()
    assert len(battle_model.get_combatants()) == 0

def test_get_battle_score(battle_model, sample_meal1):
    """Test the score calculation for a combatant."""
    score = battle_model.get_battle_score(sample_meal1)
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - 2  # MED difficulty modifier
    assert score == expected_score

def test_get_combatants(battle_model, sample_meal1, sample_meal2):
    """Test retrieving the combatants list."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    combatants = battle_model.get_combatants()
    assert combatants == [sample_meal1, sample_meal2]
