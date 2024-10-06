from typing import Optional

from wildlife_tracker.migration_tracking.migration_path import MigrationPath
from wildlife_tracker.habitat_management.habitat import Habitat

class MigrationPath: 
    def __init__ (self,
                migration_path: MigrationPath,
                species: str,
                path_id: int,
                destination: Habitat,
                start_date: str,
                start_location: Habitat,
                status: str = "Scheduled") -> None: 
        self.migration_path = migration_path
        self.species = species
        self.path_id = path_id
        self.destination = destination
        self.start_date = start_date
        self.start_location = start_location
        self.status = status

    def get_migration_path_details(path_id) -> dict:
        pass

    def update_migration_path_details(path_id: int, **kwargs) -> None:
        pass
