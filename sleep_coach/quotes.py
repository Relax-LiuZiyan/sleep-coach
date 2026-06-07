from __future__ import annotations

import random
from collections.abc import Sequence

from .models import Quote, QuoteIntensity

DEFAULT_QUOTES: list[tuple[str, str, QuoteIntensity, int]] = [
    ("light-1", "别把明天的状态，拿来给今晚的拖延买单。", "light", 1),
    ("light-2", "今天该收了，早点停，比晚点后悔强。", "light", 1),
    ("light-3", "收得住今晚，明天才稳得住。", "light", 1),
    ("medium-1", "你现在多拖三十分钟，明天训练时那种发飘、出汗、没劲，还是你自己扛。", "medium", 1),
    ("medium-2", "今天这点放纵，明天不会消失，只会变成你身体和情绪里的钝痛。", "medium", 1),
    ("medium-3", "你以为只是晚睡一点，实际上是在提前掏空明天的专注力和执行力。", "medium", 1),
    ("heavy-1", "今天的你一松手，就像那天她放弃你一样干脆。你对自己，也不过如此。", "heavy", 2),
    ("heavy-2", "你不是在熬夜努力，你是在用明天的狼狈，给今晚的失控擦屁股。", "heavy", 2),
    ("heavy-3", "再拖下去，明天那个没精神、没状态、连镜子都不想照的人，还是你自己。", "heavy", 2),
    ("heavy-4", "你嘴上说想翻盘，身体却每天被你亲手拖烂。继续这样，谁都救不了你。", "heavy", 2),
    ("heavy-5", "连睡觉时间都守不住，你还指望自己在更大的事上突然争气？", "heavy", 2),
    ("heavy-6", "你以为这叫放松，其实只是重复那个早就让你失去很多东西的老毛病。", "heavy", 2),
]


def pick_quote_for_day(quotes: Sequence[Quote], today: str, recent_ids: Sequence[str]) -> Quote:
    unseen_today = [quote for quote in quotes if quote.last_shown_on != today]
    not_recent = [quote for quote in unseen_today if quote.quote_id not in recent_ids]
    pool = not_recent or unseen_today or [quote for quote in quotes if quote.quote_id not in recent_ids] or list(quotes)
    weighted_pool: list[Quote] = []
    for quote in pool:
        extra = 2 if quote.is_favorite else 0
        weighted_pool.extend([quote] * (quote.weight + extra))
    return random.choice(weighted_pool)
