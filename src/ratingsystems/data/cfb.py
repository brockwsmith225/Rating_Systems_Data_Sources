from typing import Type

import cfbd

from ratingsystems import Bracket, DataSource, Game
from ratingsystems.core.util import FilterList 

from ratingsystems.data.model import FootballPlay


class CFBDataSource(DataSource):

    name: str = "cfb"
    plays_class: Type = FootballPlay

    def fetch(self) -> list[Game]:
        configuration = cfbd.Configuration(
            access_token=self.auth_token
        )
        games_api = cfbd.GamesApi(cfbd.ApiClient(configuration))
        plays_api = cfbd.PlaysApi(cfbd.ApiClient(configuration))

        data = []
        for week in range(1, 18):
            data.extend(games_api.get_games(self.year, week, classification="fbs", season_type="both"))

        plays = []
        for week in range(1, 18):
            plays.extend(plays_api.get_plays(self.year, week, classification="fbs", season_type="both"))
        plays = FilterList([
            FootballPlay(
                id=play.id,
                game_id=play.game_id,
                drive_id=play.drive_id,
                drive_number=play.drive_number,
                play_number=play.play_number,
                offense=play.offense,
                offense_conference=play.offense_conference,
                offense_score=play.offense_score,
                defense=play.defense,
                defense_conference=play.defense_conference,
                defense_score=play.defense_score,
                home=play.home,
                away=play.away,
                yards_to_goal=play.yards_to_goal,
                down=play.down,
                distance=play.distance,
                yards_gained=play.yards_gained,
                scoring=play.scoring,
                play_type=play.play_type,
                play_text=play.play_text,
            )
            for play in plays
        ])

        # Fix yards_gained on penalties
        drives = plays.split("drive_id")
        count = 0
        play_ids = set()
        for drive in drives.values():
            # TODO: split by game to allow correction on the last play of drives
            for play in sorted(drive.filter(admin=False, other=False), key=lambda p: p.play_number):
                if play.id in play_ids:
                    # Duplicate play with dupliate IDs
                    play.play_type = "Uncategorized"
                else:
                    play_ids.add(play.id)

                if play.yards_to_goal < 0:
                    play.yards_to_goal *= -1
                if play.distance < 0:
                    play.distance *= -1
                if play.yards_gained < 0:
                    play.yards_gained *= -1

                # if not play.penalty and play.play_text and "penalty" in play.play_text.lower() and "decline" not in play.play_text.lower():
                #     print(play)
                #     print()
                #     count += 1
                #     play.play_type = "Penalty"

                if play.scrimmage and play.distance == 0:
                    play.distance = 1

                if play.passing and not play.passing_completed:
                    play.yards_gained = 0

                next_play = [p for p in drive if p.play_number == play.play_number + 1]

                while next_play and next_play[0].admin:
                    if next_play[0].timeout or next_play[0].play_type in ["Start of Period", "End Period"]:
                        next_play = [p for p in drive if p.play_number == next_play[0].play_number + 1]
                    else:
                        break

                # TODO: on turnovers check that the offense actually turned the ball over (kickoffs may need to have offense/defense flipped) or make a kickoff fumble play type

                if not next_play:
                    # Check that play should end the drive
                    if not play.scoring and not play.turnover and play.down != 4:
                        if any([p.scoring or p.turnover or (p.down == 4 and p.yards_gained < p.distance) for p in drive if p.play_number < play.play_number]):
                            # Extra point or out of order play
                            # print()
                            # print(play)
                            # print([p for p in drive if p.scoring or p.turnover or (p.down == 4 and p.yards_gained < p.distance)])
                            # print()
                            # count += 1
                            pass
                        elif play.play_type == "Fumble Recovery (Own)":
                            # Fix label on a fumble that is lost
                            play.play_type = "Fumble"
                        elif play.penalty:
                            #     print()
                            #     print(play)
                            #     print([p.play_number for p in drive])
                            #     print()
                            #     count += 1
                            pass

                if play.punt or play.turnover:
                    next_drive = sorted([p for d in drives.values() for p in d if p.game_id == play.game_id and p.drive_number == play.drive_number + 1], key=lambda p: p.play_number)
                    if next_drive:
                        next_drive = next_drive[0]
                        play.yards_gained = next_drive.yards_to_goal - (100 - play.yards_to_goal)

                if not next_play:
                    continue

                next_play = next_play[0]

                if play.down == next_play.down and play.distance == next_play.distance and play.yards_to_goal == next_play.yards_to_goal and play.yards_gained == next_play.yards_gained and play.play_type == next_play.play_type and play.play_text == next_play.play_text:
                    # Duplicate play with unique IDs
                    play.play_type = "Uncategorized"

                if play.kickoff:
                    play.yards_gained = 100 - next_play.yards_to_goal
                    if next_play.offense == play.offense:
                        play.offense = next_play.defense
                        play.defense = next_play.offense

                # Try to correct play stats when everything else lines up
                if play.scrimmage and (next_play.scrimmage or next_play.pat or next_play.field_goal_attempt or next_play.punt):
                    expected_yards_to_goal = play.yards_to_goal - play.yards_gained
                    expected_distance = play.distance - play.yards_gained
                    expected_down = play.down + 1
                    if expected_distance <= 0:
                        expected_distance = 10
                        expected_down = 1

                    if expected_yards_to_goal != next_play.yards_to_goal:
                        if next_play.yards_to_goal == play.yards_to_goal + play.yards_gained and next_play.distance == play.distance + play.yards_gained and expected_down == next_play.down:
                            # Check if yards gained was inverted
                            play.yards_gained = -1 * play.yards_gained
                            # pass

                        elif expected_distance == next_play.distance:
                            # Check if yards to goal was incorrect
                            # TODO: check 3 in a row to see if both sides agree
                            # print()
                            # print(play.yards_to_goal)
                            # print(play.yards_gained)
                            # print(f"{play.play_type} {play.play_text}")
                            # print(next_play.yards_to_goal)
                            # print(play)
                            # print(next_play)
                            # print()
                            # count += 1
                            pass

                if play.penalty:
                    if play.yards_to_goal == 100 and next_play.kickoff:
                        play.yards_to_goal = 65
                    play.yards_gained = play.yards_to_goal - next_play.yards_to_goal

                # previous_play = [p for p in drive if p.play_number == play.play_number - 1]

                # while previous_play and previous_play[0].admin:
                #     if previous_play[0].timeout or previous_play[0].play_type in ["Start of Period", "End Period"]:
                #         previous_play = [p for p in drive if p.play_number == previous_play[0].play_number - 1]
                #     else:
                #         break

                # if not previous_play:
                #     continue

                # previous_play = previous_play[0]

                # if previous_play.scrimmage and (play.scrimmage or play.field_goal_attempt or play.punt):
                #     expected_yards_to_goal = previous_play.yards_to_goal - previous_play.yards_gained
                #     expected_distance = previous_play.distance - previous_play.yards_gained
                #     expected_down = previous_play.down + 1
                #     if expected_distance <= 0:
                #         expected_distance = 10
                #         expected_down = 1

                #     if play.down != expected_down and play.down != previous_play.down:
                #         # The down is wrong and cannot be explained by a penalty
                #         if play.yards_to_goal == expected_yards_to_goal and play.distance == expected_distance:
                #             play.down = expected_down

        plays = drives.join()

        print(count)

        game_plays = plays.split("game_id")

        # Drop games that had all of the plays assigned to the same offense
        # TODO: can I do anything to fix these games?
        game_plays = {id: game for id, game in game_plays.items() if len(set([p.offense for p in game if not p.kickoff])) == 2}

        # TODO: async

        games = []
        missing_plays = 0
        for game in data:
            if game.home_classification != cfbd.models.DivisionClassification.FBS or game.away_classification != cfbd.models.DivisionClassification.FBS:
                # Only inlucde FBS vs FBS games
                continue

            if game.id not in game_plays:
                missing_plays += 1

            games.append(
                Game(
                    id=game.id,
                    season=game.season,
                    home_team=game.home_team,
                    away_team=game.away_team,
                    week=game.week,
                    preseason=False,
                    postseason=game.season_type == cfbd.models.SeasonType.POSTSEASON,
                    start_date=game.start_date,
                    neutral_site=game.neutral_site,
                    conference_game=game.conference_game,
                    complete=game.completed,
                    overtime=None,
                    home_conference=game.home_conference,
                    home_seed=game.playoff.home_seed if hasattr(game, "playoff") and game.playoff is not None else None,
                    home_points=game.home_points,
                    home_period_points=game.home_line_scores,
                    home_stats=None,
                    away_conference=game.away_conference,
                    away_seed=game.playoff.away_seed if hasattr(game, "playoff") and game.playoff is not None else None,
                    away_points=game.away_points,
                    away_period_points=game.away_line_scores,
                    away_stats=None,
                    plays=game_plays.get(game.id, FilterList())
                )
            )

        if missing_plays > 0:
            print(f"Warning: missing plays for {missing_plays} games")

        return games
