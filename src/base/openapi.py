from collections import defaultdict
from typing import Dict, Any, Type, List

from .api_exception import APIException


def generate_responses(
    *exceptions: Type[APIException],
) -> Dict[int | str, Dict[str, Any]]:
    grouped_exceptions: Dict[int, List[Type[APIException]]] = defaultdict(list)
    for exc in exceptions:
        grouped_exceptions[exc.status_code].append(exc)

    final_responses: Dict[int | str, Dict[str, Any]] = {}

    for status_code, exc_list in grouped_exceptions.items():
        description = "<br><br>**OR**<br><br>".join(
            [exc.description for exc in exc_list]
        )

        examples = {
            exc.__name__: {
                "summary": exc.description,
                "value": exc.example,
            }
            for exc in exc_list
        }

        final_responses[status_code] = {
            "description": description,
            "content": {"application/json": {"examples": examples}},
        }

    return final_responses
