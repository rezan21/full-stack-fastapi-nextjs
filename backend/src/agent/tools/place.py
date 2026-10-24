from ag_ui.core import Tool
from pydantic import BaseModel, Field


class Place(BaseModel):
    place: str = Field(
        min_length=1, max_length=80, description="The place's name, such as London"
    )
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


FLY_TO = Tool(
    name="fly_to",
    description=(
        "Move the map the user is looking at to a place. "
        "Give the place's name and its latitude and longitude."
    ),
    parameters=Place.model_json_schema(),
)

BROWSER_TOOLS = [FLY_TO]
CONTRACT_MODELS: list[type[BaseModel]] = [Place]
