import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.catalog import GAMES

def test_game_count(): assert len(GAMES) == 50
def test_unique_ids(): assert len({g["game_id"] for g in GAMES}) == len(GAMES)
def test_required_fields():
    req={"game_id","title","players_min","players_max","play_time_min","play_time_max","age","difficulty","strategy","luck","conversation","excitement","cooperation","beginner","couple","family","children","large_group","party","short_play","description","appeal","how_to_play","recommended_scene","rakuten_query"}
    for g in GAMES:
        assert req <= set(g), g["game_id"]
        assert g["players_min"] <= g["players_max"]
        assert g["play_time_min"] <= g["play_time_max"]
        assert 3 <= len(g["how_to_play"]) <= 5
        for k in ["difficulty","strategy","luck","conversation","excitement","cooperation","beginner","couple","family","children","large_group","party","short_play"]:
            assert 0 <= g[k] <= 5
