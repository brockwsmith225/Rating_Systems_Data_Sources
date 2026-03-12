from typing import Type

import cbbd
from ratingsystems import Bracket, DataSource, Game

from ratingsystems.data.model import BasketballGameStats


class CBBDataSource(DataSource):

    name: str = "cbb"
    stats_class: Type = BasketballGameStats

    def fetch(self) -> list[Game]:
        configuration = cbbd.Configuration(
            access_token=self.auth_token
        )
        games_api = cbbd.GamesApi(cbbd.ApiClient(configuration))

        data = []
        data.extend(games_api.get_game_teams(season=self.year, season_type="regular", start_date_range=f"{self.year-1}-11-01T00:00:00", end_date_range=f"{self.year-1}-11-30T23:59:59"))
        data.extend(games_api.get_game_teams(season=self.year, season_type="regular", start_date_range=f"{self.year-1}-12-01T00:00:00", end_date_range=f"{self.year-1}-12-31T23:59:59"))
        data.extend(games_api.get_game_teams(season=self.year, season_type="regular", start_date_range=f"{self.year}-01-01T00:00:00", end_date_range=f"{self.year}-01-31T23:59:59"))
        data.extend(games_api.get_game_teams(season=self.year, season_type="regular", start_date_range=f"{self.year}-02-01T00:00:00", end_date_range=f"{self.year}-02-28T23:59:59"))
        data.extend(games_api.get_game_teams(season=self.year, season_type="regular", start_date_range=f"{self.year}-03-01T00:00:00", end_date_range=f"{self.year}-03-31T23:59:59"))
        data.extend(games_api.get_game_teams(season=self.year, season_type="postseason", start_date_range=f"{self.year}-03-01T00:00:00", end_date_range=f"{self.year}-03-31T23:59:59"))

        games = []
        for game in data:
            if not game.is_home:
                # Games show up twice, once for each team, so remove duplicates by only looking at the home team's game
                continue

            if game.conference is None or game.opponent_conference is None:
                # Only inlucde D1 vs D1 games
                continue

            games.append(
                Game(
                    id=game.game_id,
                    season=game.season,
                    home_team=game.team,
                    away_team=game.opponent,
                    preseason=game.game_type == cbbd.models.SeasonType.PRESEASON,
                    postseason=game.game_type == cbbd.models.SeasonType.POSTSEASON,
                    start_date=game.start_date,
                    neutral_site=game.neutral_site,
                    conference_game=game.conference_game,
                    complete=game.game_minutes is not None,
                    overtime=game.game_minutes > 40 if game.game_minutes is not None else None,
                    home_conference=game.conference,
                    home_seed=game.team_seed,
                    home_points=game.team_stats.points.total,
                    home_period_points=game.team_stats.points.by_period,
                    home_stats=BasketballGameStats(
                        points=game.team_stats.points.total,
                        period_points=game.team_stats.points.by_period,
                        field_goals_made=game.team_stats.field_goals.made,
                        field_goals_attempted=game.team_stats.field_goals.attempted,
                        field_goals_pct=game.team_stats.field_goals.pct,
                        two_point_field_goals_made=game.team_stats.two_point_field_goals.made,
                        two_point_field_goals_attempted=game.team_stats.two_point_field_goals.attempted,
                        two_point_field_goals_pct=game.team_stats.two_point_field_goals.pct,
                        three_point_field_goals_made=game.team_stats.three_point_field_goals.made,
                        three_point_field_goals_attempted=game.team_stats.three_point_field_goals.attempted,
                        three_point_field_goals_pct=game.team_stats.three_point_field_goals.pct,
                        free_throws_made=game.team_stats.free_throws.made,
                        free_throws_attempted=game.team_stats.free_throws.attempted,
                        free_throws_pct=game.team_stats.free_throws.pct,
                        total_rebounds=game.team_stats.rebounds.total,
                        offensive_rebounds=game.team_stats.rebounds.offensive,
                        defensive_rebounds=game.team_stats.rebounds.defensive,
                        turnovers=game.team_stats.turnovers.total,
                        fouls=game.team_stats.fouls.total,
                        assists=game.team_stats.assists,
                        blocks=game.team_stats.blocks,
                        steals=game.team_stats.steals,
                        possessions=game.team_stats.possessions,
                    ),
                    away_conference=game.opponent_conference,
                    away_seed=game.opponent_seed,
                    away_points=game.opponent_stats.points.total,
                    away_period_points=game.opponent_stats.points.by_period,
                    away_stats=BasketballGameStats(
                        points=game.opponent_stats.points.total,
                        period_points=game.opponent_stats.points.by_period,
                        field_goals_made=game.opponent_stats.field_goals.made,
                        field_goals_attempted=game.opponent_stats.field_goals.attempted,
                        field_goals_pct=game.opponent_stats.field_goals.pct,
                        two_point_field_goals_made=game.opponent_stats.two_point_field_goals.made,
                        two_point_field_goals_attempted=game.opponent_stats.two_point_field_goals.attempted,
                        two_point_field_goals_pct=game.opponent_stats.two_point_field_goals.pct,
                        three_point_field_goals_made=game.opponent_stats.three_point_field_goals.made,
                        three_point_field_goals_attempted=game.opponent_stats.three_point_field_goals.attempted,
                        three_point_field_goals_pct=game.opponent_stats.three_point_field_goals.pct,
                        free_throws_made=game.opponent_stats.free_throws.made,
                        free_throws_attempted=game.opponent_stats.free_throws.attempted,
                        free_throws_pct=game.opponent_stats.free_throws.pct,
                        total_rebounds=game.opponent_stats.rebounds.total,
                        offensive_rebounds=game.opponent_stats.rebounds.offensive,
                        defensive_rebounds=game.opponent_stats.rebounds.defensive,
                        turnovers=game.opponent_stats.turnovers.total,
                        fouls=game.opponent_stats.fouls.total,
                        assists=game.opponent_stats.assists,
                        blocks=game.opponent_stats.blocks,
                        steals=game.opponent_stats.steals,
                        possessions=game.opponent_stats.possessions,
                    ),
                )
            )
        return games
