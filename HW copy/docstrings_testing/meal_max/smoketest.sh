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
  response=$(curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"id\":\"$id\", \"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}")
  if echo "$response" | grep -q '"status": "combatant added"'; then
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
  if echo "$response" | grep -q '"status": "meal deleted"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
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
  meal_name=$1

  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal_name")
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
  echo "Getting meal leaderboard sorted by (wins)..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard")
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

###############################################
#
# Battle Management
#
###############################################

prep_combatant1() {
  meal=$1
  cuisine=$2
  price=$3

  echo "Preparing first combatant ($meal) for battle..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price}")
  if echo "$response" | grep -q '"status": "combatant prepared"'; then
    echo "Combatant prepared successfully with meal ($meal)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatant JSON (meal $meal):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to prepare combatant with meal ($meal)."
    exit 1
  fi
}

prep_combatant2() {
  meal=$1
  cuisine=$2
  price=$3

  echo "Preparing second combatant ($meal) for battle..."

  response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price}")
  if echo "$response" | grep -q '"status": "combatant prepared"'; then
    echo "Combatant prepared successfully with meal ($meal)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatant JSON (meal $meal):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to prepare combatant with meal ($meal)."
    exit 1
  fi
}


# Starts a battle between combatants
start_battle() {
  echo "Starting a battle between prepared combatants..."
  response=$(curl -s -X GET "$BASE_URL/battle")
  if echo "$response" | grep -q '"status": "battle complete"'; then
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

get_combatants() {
  echo "Getting combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get combatants."
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing all combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")
  if echo "$response" | grep -q '"status": "combatants cleared"'; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

clear_meals() {
  echo "Clearing all meals..."
  response=$(curl -s -X DELETE "$BASE_URL/clear-meals")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meals cleared successfully."
  else
    echo "Failed to clear meals."
    exit 1
  fi
}


# Health checks
check_health
check_db

# create meal
create_meal 1 "Pasta" "Italian" 20 "LOW"
create_meal 2 "Sushi" "Japanese" 50 "MED"
create_meal 3 "Enchilada" "Mexican" 10 "HIGH"
create_meal 4 "Hamburger" "American" 15 "MED"
create_meal 5 "Pizza" "Italian" 25 "LOW"

delete_meal_by_id 1

get_meal_by_id 2
get_meal_by_name "Pizza"

prep_combatant1 "Hamburger" "American" 15 "MED"
prep_combatant2 "Pizza" "Italian" 25 "LOW"

get_combatants

start_battle

get_meal_leaderboard_wins

clear_combatants

clear_meals

echo "All tests passed successfully!"