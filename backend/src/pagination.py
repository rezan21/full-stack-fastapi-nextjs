from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query

MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Pagination:
    skip: int
    limit: int


async def get_pagination(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = MAX_PAGE_SIZE,
) -> Pagination:
    """Return the page the query parameters ask for."""
    return Pagination(skip=skip, limit=limit)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]
