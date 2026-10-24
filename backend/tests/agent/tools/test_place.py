from src.agent.tools.place import FLY_TO


def test_the_model_is_given_the_limits_the_browser_checks() -> None:
    parameters = FLY_TO.parameters or {}

    assert parameters["properties"]["place"]["maxLength"] == 80
    lat = parameters["properties"]["lat"]
    assert (lat["minimum"], lat["maximum"]) == (-90, 90)
