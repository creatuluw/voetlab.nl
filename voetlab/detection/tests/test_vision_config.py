"""T8 — vision config factory (drop COCO class 32 → football-ball model; SAHI hook)."""
from voetlab.detection.detect import BALL, PERSON, build_vision_config


def test_defaults():
    c = build_vision_config()
    assert c["classes"] == [PERSON, BALL]
    assert c["conf"] == 0.25
    assert c["imgsz"] == 1280
    assert c["sahi"] is False


def test_override_for_football_ball_model():
    c = build_vision_config(classes=[0, 1], ball_model_path="football-ball.pt", sahi=True, conf=0.15)
    assert c["classes"] == [0, 1]
    assert c["ball_model_path"] == "football-ball.pt"
    assert c["sahi"] is True
    assert c["conf"] == 0.15
