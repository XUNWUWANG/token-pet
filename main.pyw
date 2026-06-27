"""TokenPet — Codex 用量桌宠。

实时监测 Codex Token 用量和 DeepSeek 账户余额。

用法：
    python main.pyw
    # 或双击 main.pyw
"""

﻿# main.pyw — 无终端窗口版入口
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pet.config import load_config, find_env_file
from pet.app import PetWindow

env_file = find_env_file()
if not env_file.exists():
    example = env_file.with_suffix('.example')
    if example.exists():
        import shutil
        shutil.copy2(example, env_file)

config = load_config(str(env_file) if env_file.exists() else None)
pet = PetWindow(config)
pet.run()
