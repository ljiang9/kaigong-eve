#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kaigong-eve 开工前夜模拟器.

时间:2026 年 10 月 7 日 18:00 → 24:00.
背景:国庆 7 天假期最后一天,明天 10 月 8 日开工,
且 10 月 10 日(周六)还要调休上班.致敬全网"开工前夜"emo 玩梗.

纯 Python 标准库,无第三方依赖,Python 3.10+.
"""

from __future__ import annotations

import argparse
import random
import sys

GAME_TITLE = "开工前夜"
SUBTITLE = "10月7日 18:00 → 24:00 · 明天 10月8日开工 · 10月10日周六调休上班"

SLOT_TITLES = [
    "18:00 晚饭吃什么",
    "20:00 收拾行李",
    "21:00 工作消息",
    "22:00 调闹钟",
    "23:00 再刷会儿手机",
]


class IllegalChoice(Exception):
    """非法选项(不存在的选项编号或时段)."""


def clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    """把属性值钳制在 [lo, hi] 区间."""
    return max(lo, min(hi, value))


class Night:
    """开工前夜的状态机:6 个时段,三维属性."""

    def __init__(self, rng: random.Random | None = None, event_chance: float = 0.30):
        self.rng = rng if rng is not None else random.Random()
        self.event_chance = event_chance
        self.battery = 70      # 心理电量 0-100
        self.packing = 20      # 行李收拾度 0-100
        self.read_msgs = 0     # 工作消息已读数
        self.unread = 99       # 工作消息未读数
        self.tomorrow_crit = False  # "明天暴击预定"
        self.log: list[str] = []

    def say(self, msg: str) -> None:
        self.log.append(msg)

    def _bump(self, db: int = 0, dp: int = 0) -> None:
        self.battery = clamp(self.battery + db)
        self.packing = clamp(self.packing + dp)

    def options(self, slot: int) -> list[tuple[str, str]]:
        table = {
            0: [("1", "点外卖,快乐加餐"), ("2", "翻冰箱剩菜对付一口")],
            1: [("1", "全部塞进行李箱,一口气收完"), ("2", "明天再说,先躺平")],
            2: [("1", "点开 99+ 未读,直面现实"), ("2", "装没看见,明天再说")],
            3: [("1", "调 3 个闹钟,万无一失"), ("2", "我相信生物钟")],
            4: [("1", "再刷 1 小时手机"), ("2", "现在就睡,养生开工")],
        }
        if slot not in table:
            raise IllegalChoice(f"未知时段: {slot}")
        return table[slot]

    def choose(self, slot: int, key: str) -> str:
        keys = [k for k, _ in self.options(slot)]
        if key not in keys:
            raise IllegalChoice(f"非法选项: {key!r}(本时段可选 {keys})")
        handler = {
            0: self._dinner,
            1: self._pack,
            2: self._messages,
            3: self._alarm,
            4: self._phone,
        }[slot]
        note = handler(key)
        self.say(note)
        self._maybe_event()
        return note

    # -- 各时段选项效果 --
    def _dinner(self, key: str) -> str:
        if key == "1":
            self._bump(db=15)
            return "外卖到了,热气腾腾。心理电量 +15。"
        self._bump(db=-10, dp=10)
        return "剩菜清空,冰箱倒是收拾干净了。电量 -10,收拾度 +10。"

    def _pack(self, key: str) -> str:
        if key == "1":
            self._bump(db=-15, dp=50)
            return "行李箱被塞到拉不上拉链。收拾度 +50,电量 -15。"
        self._bump(db=10, dp=-10)
        return "往床上一瘫:明天的事明天再说。电量 +10,收拾度 -10。"

    def _messages(self, key: str) -> str:
        if key == "1":
            self.read_msgs += self.unread
            self.unread = 0
            self._bump(db=-25)
            return "99+ 条未读全部点开,每一条都在 @你。电量暴击 -25。"
        self.tomorrow_crit = True
        self._bump(db=10)
        return "把手机扣在桌上:我什么都没看见。电量 +10(明天暴击预定)。"

    def _alarm(self, key: str) -> str:
        if key == "1":
            self._bump(db=5)
            return "3 个闹钟,间隔 5 分钟,万无一失。电量 +5。"
        self.tomorrow_crit = True
        self._bump(db=5)
        return "“我的生物钟比闹钟靠谱。”电量 +5(起床暴击预定)。"

    def _phone(self, key: str) -> str:
        if key == "1":
            self.tomorrow_crit = True
            self._bump(db=10)
            return "再刷 1 小时……1 小时后又 1 小时。电量 +10(熬夜暴击预定)。"
        self._bump(db=15)
        return "放下手机,闭眼。电量 +15,养生开工第一步。"

    # -- 随机事件 --
    def _maybe_event(self) -> None:
        if self.rng.random() >= self.event_chance:
            return
        which = self.rng.choice(["boss", "mom", "techan"])
        if which == "boss":
            self._bump(db=-20)
            self.read_msgs += 1
            self.say("【随机事件】老板深夜发来两个字:「在吗」。电量 -20,已读 +1。")
        elif which == "mom":
            self._bump(db=-10, dp=5)
            self.say("【随机事件】妈妈来电:「什么时候回来上班啊?」电量 -10,收拾度 +5。")
        else:
            self._bump(db=-10, dp=-15)
            self.say("【随机事件】突然想起:假期带的特产还没送完!电量 -10,收拾度 -15。")

    # -- 终局结算 --
    def ending(self) -> tuple[str, str]:
        if self.battery >= 70 and self.packing >= 50:
            return "满血开工", "电量拉满,行李就绪,明天工位见!"
        if self.battery < 35:
            return "丧尸开工", "电量见底,明天全靠咖啡续命。"
        if self.packing < 30:
            return "请假预备役", "行李都没收拾完,要不……请天假?"
        return "调休受害者plus", "今晚状态还行,但别忘了:10月10日周六还要调休上班。"


def auto_game(seed: int, game_index: int, event_chance: float = 0.30):
    """AI 自动玩一局:每时段随机选。返回 (Night, 结局标题, 结局评语)."""
    rng = random.Random(seed + game_index)
    night = Night(rng=rng, event_chance=event_chance)
    for slot in range(5):
        keys = [k for k, _ in night.options(slot)]
        night.choose(slot, rng.choice(keys))
    title, comment = night.ending()
    return night, title, comment


def run_auto(games: int, seed: int, verbose: bool) -> int:
    from collections import Counter

    dist: Counter[str] = Counter()
    for i in range(games):
        night, title, comment = auto_game(seed, i)
        dist[title] += 1
        if verbose:
            print(f"=== 第 {i + 1} 局(seed={seed + i}) ===")
            for line in night.log:
                print("  " + line)
            print(f"  终局:电量 {night.battery},收拾度 {night.packing},"
                  f"工作消息已读 {night.read_msgs}")
            print(f"  结局:{title} —— {comment}")
    print(f"\n共 {games} 局,结局分布:")
    for title, cnt in dist.most_common():
        print(f"  {title}: {cnt} 局")
    return 0


def run_interactive() -> int:
    night = Night()
    print(GAME_TITLE)
    print(SUBTITLE)
    for slot in range(5):
        print(f"\n【{SLOT_TITLES[slot]}】(电量 {night.battery} / 收拾度 {night.packing})")
        for key, label in night.options(slot):
            print(f"  {key}. {label}")
        try:
            key = input("你的选择: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出,祝明天开工顺利。")
            return 0
        try:
            print(night.choose(slot, key))
        except IllegalChoice as exc:
            print(f"无效输入({exc}),本时段跳过。")
    title, comment = night.ending()
    print(f"\n【24:00 终局】电量 {night.battery},收拾度 {night.packing},"
          f"工作消息已读 {night.read_msgs}")
    print(f"结局:{title} —— {comment}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="开工前夜模拟器:10月7日 18:00→24:00 的心理建设。")
    p.add_argument("--auto", action="store_true", help="自动演示模式(AI 随机选择)")
    p.add_argument("--games", type=int, default=1, help="自动演示局数(默认 1)")
    p.add_argument("--seed", type=int, default=42, help="随机种子(默认 42)")
    p.add_argument("--verbose", action="store_true", help="打印整晚战报")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.games < 1:
        print("games 须 ≥ 1", file=sys.stderr)
        return 2
    if args.auto:
        return run_auto(args.games, args.seed, args.verbose)
    if not sys.stdin.isatty():
        print("交互模式需要终端运行;非终端请使用 --auto 自动演示。", file=sys.stderr)
        return 2
    return run_interactive()


if __name__ == "__main__":
    sys.exit(main())
