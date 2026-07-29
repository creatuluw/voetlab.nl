"""T11 — pitch-control surface (synthetic metric positions, no real data)."""

import numpy as np

from voetlab.tactics.pitch_control import compute_pitch_control


def _player(x, y, team, vx=0.0, vy=0.0):
    return {"x": x, "y": y, "vx": vx, "vy": vy, "team": team}


def test_surface_is_a_probability_field():
    players = [_player(40, 34, "A"), _player(60, 34, "B")]
    surface = compute_pitch_control(players, ball_xy=(50, 34))
    assert isinstance(surface, np.ndarray)
    assert surface.shape == (68, 105)           # default 105x68 m pitch at 1 m step
    assert surface.min() >= 0.0
    assert surface.max() <= 1.0


def test_attacker_near_ball_dominates_local_surface():
    # One attacker on the ball; a lone defender far across the pitch.
    players = [_player(20, 34, "A", vx=2.0, vy=0.0), _player(90, 34, "B")]
    surface = compute_pitch_control(players, ball_xy=(20, 34))
    assert surface[34, 20] > 0.5                 # right on the attacker → team A controls
    assert surface[34, 90] < 0.5                 # near the far defender → team A does not


def test_two_defenders_drop_team_a_control_at_target():
    # Attacker holds the ball near the left goal; a target point up the pitch is screened
    # by two team-B defenders standing between the ball and the target.
    players = [
        _player(10, 34, "A", vx=3.0, vy=0.0),
        _player(30, 32, "B"),
        _player(30, 36, "B"),
    ]
    surface = compute_pitch_control(players, ball_xy=(10, 34))
    assert surface[34, 10] > 0.5                 # attacker keeps the ball
    assert surface[34, 40] < 0.5                 # screened target → team A loses it
