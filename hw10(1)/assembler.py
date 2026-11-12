#!/usr/bin/env python3
"""Nand2Tetris Hack 組譯器 (Project 6)

用法: python3 assembler.py Prog.asm   ->  產生 Prog.hack
"""
import sys
import os

# ---------- 指令對照表 ----------
_COMP_A = {  # a = 0
    "0": "101010", "1": "111111", "-1": "111010",
    "D": "001100", "A": "110000", "!D": "001101", "!A": "110001",
    "-D": "001111", "-A": "110011", "D+1": "011111", "A+1": "110111",
    "D-1": "001110", "A-1": "110010", "D+A": "000010", "D-A": "010011",
    "A-D": "000111", "D&A": "000000", "D|A": "010101",
}
COMP = {k: "0" + v for k, v in _COMP_A.items()}
# a = 1:把 A 換成 M
COMP.update({k.replace("A", "M"): "1" + v for k, v in _COMP_A.items() if "A" in k})
# 交換律的別名 (例如 A+D、1+D)
ALIASES = {"A+D": "D+A", "M+D": "D+M", "A&D": "D&A", "M&D": "D&M",
           "A|D": "D|A", "M|D": "D|M", "1+D": "D+1", "1+A": "A+1", "1+M": "M+1"}
for alias, real in ALIASES.items():
    COMP[alias] = COMP[real]

DEST = {"": "000", "M": "001", "D": "010", "MD": "011",
        "A": "100", "AM": "101", "AD": "110", "AMD": "111"}
DEST["DM"] = DEST["MD"]
DEST["MA"] = DEST["AM"]
DEST["DA"] = DEST["AD"]

JUMP = {"": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
        "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"}

PREDEFINED = {"SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
              "SCREEN": 16384, "KBD": 24576}
PREDEFINED.update({f"R{i}": i for i in range(16)})


class AsmError(Exception):
    pass


def clean(line):
    """移除註解與所有空白。"""
    line = line.split("//", 1)[0]
    return "".join(line.split())


def encode_c(instr):
    dest, comp, jump = "", instr, ""
    if "=" in comp:
        dest, comp = comp.split("=", 1)
    if ";" in comp:
        comp, jump = comp.split(";", 1)
    if dest not in DEST or comp not in COMP or jump not in JUMP:
        raise AsmError(f"無效的 C 指令: {instr}")
    return "111" + COMP[comp] + DEST[dest] + JUMP[jump]


def assemble(lines):
    # --- 第一輪:建立符號表 (記錄標籤 (LABEL) 的位址) ---
    symbols = dict(PREDEFINED)
    program = []
    for n, raw in enumerate(lines, 1):
        line = clean(raw)
        if not line:
            continue
        if line.startswith("("):
            if not line.endswith(")"):
                raise AsmError(f"第 {n} 行: 標籤格式錯誤: {line}")
            label = line[1:-1]
            if label in symbols:
                raise AsmError(f"第 {n} 行: 重複定義的符號: {label}")
            symbols[label] = len(program)
        else:
            program.append((n, line))

    # --- 第二輪:翻譯 ---
    next_var = 16
    output = []
    for n, line in program:
        try:
            if line.startswith("@"):
                sym = line[1:]
                if not sym:
                    raise AsmError(f"空的 A 指令")
                if sym.isdigit():
                    value = int(sym)
                else:
                    if sym not in symbols:
                        symbols[sym] = next_var
                        next_var += 1
                    value = symbols[sym]
                if value > 32767:
                    raise AsmError(f"位址超出 15 位元範圍: {value}")
                output.append(format(value, "016b"))
            else:
                output.append(encode_c(line))
        except AsmError as e:
            raise AsmError(f"第 {n} 行: {e}") from None
    return output


def main():
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".asm"):
        print("用法: python3 assembler.py Prog.asm")
        sys.exit(1)
    src = sys.argv[1]
    dst = os.path.splitext(src)[0] + ".hack"
    with open(src, encoding="utf-8") as f:
        lines = f.readlines()
    try:
        result = assemble(lines)
    except AsmError as e:
        print(f"錯誤: {e}")
        sys.exit(1)
    with open(dst, "w") as f:
        f.write("\n".join(result) + "\n")
    print(f"完成: {dst} ({len(result)} 條指令)")


if __name__ == "__main__":
    main()