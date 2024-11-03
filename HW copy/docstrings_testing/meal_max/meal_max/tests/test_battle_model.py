import logging 
import pytest
from meal_max.models.kitchen_model import Meal
from meal_max.models.battle_model import BattleModel

@pytest.fixture
def combatant_1():
    return Meal(id=1, meal="Spaghetti", cuisine="Italian", price=10.0, difficulty="MED")

@pytest.fixture
def combatant_2():
    return Meal(id=2, meal="Sushi", cuisine="Japanese", price=15.0, difficulty="HIGH")

@pytest.fixture
def battle_model():
    return BattleModel()

def test_prep_combatant(battle_model, combatant_1, combatant_2):
    """Test adding combatants to the battle."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    
    assert len(battle_model.get_combatants()) == 2

    # Test adding more than two combatants
    with pytest.raises(ValueError, match="Combatant list is full"):
        battle_model.prep_combatant(combatant_1)

def test_battle_insufficient_combatants(battle_model, combatant_1):
    """Test battle with insufficient combatants."""
    battle_model.prep_combatant(combatant_1)
    
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle"):
        battle_model.battle()

@patch("meal_max.models.battle_model.get_random", return_value=0.1)
@patch("meal_max.models.battle_model.update_meal_stats")
def test_battle_winner(mock_update_stats, mock_get_random, battle_model, combatant_1, combatant_2):
    """Test battle outcome and stats update."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)

    # Mock scores to control the winner outcome
    with patch.object(battle_model, "get_battle_score", side_effect=[80, 60]):
        winner = battle_model.battle()
        assert winner == combatant_1.meal

    # Verify that stats were updated correctly
    mock_update_stats.assert_any_call(combatant_1.id, 'win')
    mock_update_stats.assert_any_call(combatant_2.id, 'loss')

def test_clear_combatants(battle_model, combatant_1, combatant_2):
    """Test clearing combatants."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    battle_model.clear_combatants()
    
    assert len(battle_model.get_combatants()) == 0

def test_get_battle_score(battle_model, combatant_1):
    """Test battle score calculation."""
    score = battle_model.get_battle_score(combatant_1)
    expected_score = (combatant_1.price * len(combatant_1.cuisine)) - 2  # MED difficulty modifier is 2
    assert score == expected_score

def test_get_combatants(battle_model, combatant_1, combatant_2):
    """Test retrieving combatants list."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    
    combatants = battle_model.get_combatants()
    assert combatants == [combatant_1, combatant_2]