from collections import defaultdict
from typing import Dict, List

_tasks_running_list: Dict[str, List[list]] = defaultdict(list)

value = _tasks_running_list['task_id']

print(value)