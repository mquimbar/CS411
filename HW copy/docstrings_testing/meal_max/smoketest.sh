#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Meal Management
#
##########################################################

create_meal() {
  id=$1
  meal=$2
  cuisine=$3
  price=$4
  difficulty=$5

  echo "Adding meal ($id - $meal, $cuisine) to the meal list..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"id\":\"$id\", \"meal\":\"$meal\", \"cuisine\":$cuisine, \"price\":\"$price\", \"difficulty\":$difficulty}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-database-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal_name=$2

  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-databse-by-name/$meal_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name ($meal_name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (name $meal_name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name ($meal_name)."
    exit 1
  fi
}

get_meal_leaderboard_wins() {
  echo "Getting meal leaderboard sorted by wins..."
  response=$(curl -s -X GET "$BASE_URL/meal-leaderboard?sort_by=wins")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON (sorted by wins):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal leaderboard."
    exit 1
  fi
}

get_meal_leaderboard_win_pct() {
  echo "Getting meal leaderboard sorted by win_pct..."
  response=$(curl -s -X GET "$BASE_URL/meal-leaderboard?sort_by=win_pct")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON (sorted by win_pct):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal leaderboard."
    exit 1
  fi
}


###############################################
#
# Battle Management
#
###############################################

prep_combatant() {
  meal_id=$1
  echo "Preparing combatant with meal ID ($meal_id) for battle..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
    -d "{\"meal_id\": \"$meal_id\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant prepared successfully with meal ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatant JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to prepare combatant with meal ID ($meal_id)."
    exit 1
  fi
}

# Starts a battle between combatants
start_battle() {
  echo "Starting a battle between prepared combatants..."
  response=$(curl -s -X POST "$BASE_URL/start-battle")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle started successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle Result JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to start battle."
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing all combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

# Test adding more than two combatants
test_combatant_overflow() {
  meal_id=$1

  echo "Attempting to add a third combatant (meal ID $meal_id)..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
    -d "{\"meal_id\": \"$meal_id\"}")

  if echo "$response" | grep -q '"status": "error"' && echo "$response" | grep -q "Combatant list is full"; then
    echo "Correctly handled error for combatant overflow."
  else
    echo "Failed: was able to add more than two combatants. "
    exit 1
  fi

}
