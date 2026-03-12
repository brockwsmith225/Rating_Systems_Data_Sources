from dataclasses import dataclass, field

from ratingsystems import GameStats


@dataclass
class BasketballGameStats(GameStats):
    field_goals_made: float = field()
    field_goals_attempted: float = field()
    field_goals_pct: float = field()
    two_point_field_goals_made: float = field()
    two_point_field_goals_attempted: float = field()
    two_point_field_goals_pct: float = field()
    three_point_field_goals_made: float = field()
    three_point_field_goals_attempted: float = field()
    three_point_field_goals_pct: float = field()
    free_throws_made: float = field()
    free_throws_attempted: float = field()
    free_throws_pct: float = field()
    total_rebounds: int = field()
    offensive_rebounds: int = field()
    defensive_rebounds: int = field()
    turnovers: int = field()
    fouls: int = field()
    assists: int = field()
    blocks: int = field()
    steals: int = field()
    possessions: int = field()
