#!/usr/bin/env python3
"""
Nand2Tetris Project 11 - Jack Compiler
將 .jack 原始碼編譯為 Hack VM (.vm) 程式碼。

使用方式:
    python3 JackCompiler.py path/to/File.jack
    python3 JackCompiler.py path/to/Directory
"""

import os
import re
import sys
from enum import Enum


# =============================================================================
# 1. JackTokenizer: 詞法分析器
# =============================================================================
class TokenType(Enum):
    KEYWORD = "KEYWORD"
    SYMBOL = "SYMBOL"
    IDENTIFIER = "IDENTIFIER"
    INT_CONST = "INT_CONST"
    STRING_CONST = "STRING_CONST"


KEYWORDS = {
    "class", "constructor", "function", "method", "field", "static", "var",
    "int", "char", "boolean", "void", "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return",
}

SYMBOLS = set("{}()[].,;+-*/&|<>=~")

# 單次掃描的正則表達式，避免字串中的 // 或 /* 被誤判為註解
TOKEN_REGEX = re.compile(
    r"//[^\n]*|"                    # 單行註解
    r"/\*[\s\S]*?\*/|"              # 多行 / API 註解
    r'"([^"\n]*)"|'                 # 字串常數 (group 1)
    r"(\d+)|"                       # 整數常數 (group 2)
    r"([A-Za-z_][A-Za-z0-9_]*)|"    # 關鍵字或識別字 (group 3)
    r"([{}()\[\].,;+\-*/&|<>=~])|"  # 符號 (group 4)
    r"\s+"                          # 空白字元
)


class JackTokenizer:
    def __init__(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        self.tokens = []
        for match in TOKEN_REGEX.finditer(source):
            str_val, int_val, word_val, sym_val = match.groups()
            if str_val is not None:
                self.tokens.append((TokenType.STRING_CONST, str_val))
            elif int_val is not None:
                self.tokens.append((TokenType.INT_CONST, int(int_val)))
            elif word_val is not None:
                if word_val in KEYWORDS:
                    self.tokens.append((TokenType.KEYWORD, word_val))
                else:
                    self.tokens.append((TokenType.IDENTIFIER, word_val))
            elif sym_val is not None:
                self.tokens.append((TokenType.SYMBOL, sym_val))

        self.pos = 0

    def has_more_tokens(self) -> bool:
        return self.pos < len(self.tokens)

    def peek(self, offset: int = 0):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None, None

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok


# =============================================================================
# 2. SymbolTable: 符號表（類別與副程式雙層作用域）
# =============================================================================
class SymbolTable:
    KIND_TO_SEGMENT = {
        "STATIC": "static",
        "FIELD": "this",
        "ARG": "argument",
        "VAR": "local",
    }

    def __init__(self):
        self.class_table = {}
        self.subroutine_table = {}
        self.counts = {"STATIC": 0, "FIELD": 0, "ARG": 0, "VAR": 0}

    def start_subroutine(self):
        self.subroutine_table.clear()
        self.counts["ARG"] = 0
        self.counts["VAR"] = 0

    def define(self, name: str, var_type: str, kind: str):
        idx = self.counts[kind]
        self.counts[kind] += 1
        entry = (var_type, kind, idx)
        if kind in ("STATIC", "FIELD"):
            self.class_table[name] = entry
        else:
            self.subroutine_table[name] = entry

    def var_count(self, kind: str) -> int:
        return self.counts[kind]

    def _lookup(self, name: str):
        if name in self.subroutine_table:
            return self.subroutine_table[name]
        if name in self.class_table:
            return self.class_table[name]
        return None

    def kind_of(self, name: str):
        entry = self._lookup(name)
        return entry[1] if entry else None

    def type_of(self, name: str):
        entry = self._lookup(name)
        return entry[0] if entry else None

    def index_of(self, name: str):
        entry = self._lookup(name)
        return entry[2] if entry else None

    def segment_of(self, name: str):
        kind = self.kind_of(name)
        return self.KIND_TO_SEGMENT[kind] if kind else None


# =============================================================================
# 3. VMWriter: 虛擬機程式碼輸出器
# =============================================================================
class VMWriter:
    def __init__(self, out_filepath: str):
        self.f = open(out_filepath, "w", encoding="utf-8")

    def write_push(self, segment: str, index: int):
        self.f.write(f"push {segment} {index}\n")

    def write_pop(self, segment: str, index: int):
        self.f.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command: str):
        self.f.write(f"{command}\n")

    def write_label(self, label: str):
        self.f.write(f"label {label}\n")

    def write_goto(self, label: str):
        self.f.write(f"goto {label}\n")

    def write_if(self, label: str):
        self.f.write(f"if-goto {label}\n")

    def write_call(self, name: str, n_args: int):
        self.f.write(f"call {name} {n_args}\n")

    def write_function(self, name: str, n_locals: int):
        self.f.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.f.write("return\n")

    def close(self):
        self.f.close()


# =============================================================================
# 4. CompilationEngine: 遞迴下降語法分析與程式碼產生器
# =============================================================================
class CompilationEngine:
    BINARY_OPS = {
        "+": "add",
        "-": "sub",
        "&": "and",
        "|": "or",
        "<": "lt",
        ">": "gt",
        "=": "eq",
    }
    UNARY_OPS = {"-": "neg", "~": "not"}

    def __init__(self, tokenizer: JackTokenizer, writer: VMWriter):
        self.tk = tokenizer
        self.vm = writer
        self.st = SymbolTable()
        self.class_name = ""
        self.label_counter = 0

    def _new_label(self, prefix: str) -> str:
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def _eat(self, expected_val=None):
        ttype, val = self.tk.advance()
        if expected_val is not None and val != expected_val:
            raise SyntaxError(f"Expected '{expected_val}', got '{val}'")
        return ttype, val

    # -------------------------------------------------------------------------
    # Program Structure
    # -------------------------------------------------------------------------
    def compile_class(self):
        self._eat("class")
        _, self.class_name = self._eat()
        self._eat("{")

        while self.tk.peek()[1] in ("static", "field"):
            self.compile_class_var_dec()

        while self.tk.peek()[1] in ("constructor", "function", "method"):
            self.compile_subroutine()

        self._eat("}")

    def compile_class_var_dec(self):
        _, kind_kw = self._eat()  # 'static' or 'field'
        kind = kind_kw.upper()
        _, var_type = self._eat()
        _, var_name = self._eat()
        self.st.define(var_name, var_type, kind)

        while self.tk.peek()[1] == ",":
            self._eat(",")
            _, var_name = self._eat()
            self.st.define(var_name, var_type, kind)

        self._eat(";")

    def compile_subroutine(self):
        self.st.start_subroutine()
        _, sub_kind = self._eat()  # constructor | function | method
        self._eat()                # return type ('void' or type)
        _, sub_name = self._eat()

        # method 的第 0 個參數固定為物件本身 this
        if sub_kind == "method":
            self.st.define("this", self.class_name, "ARG")

        self._eat("(")
        self.compile_parameter_list()
        self._eat(")")

        # subroutineBody: '{' varDec* statements '}'
        self._eat("{")
        while self.tk.peek()[1] == "var":
            self.compile_var_dec()

        n_locals = self.st.var_count("VAR")
        self.vm.write_function(f"{self.class_name}.{sub_name}", n_locals)

        if sub_kind == "constructor":
            n_fields = self.st.var_count("FIELD")
            self.vm.write_push("constant", n_fields)
            self.vm.write_call("Memory.alloc", 1)
            self.vm.write_pop("pointer", 0)
        elif sub_kind == "method":
            self.vm.write_push("argument", 0)
            self.vm.write_pop("pointer", 0)

        self.compile_statements()
        self._eat("}")

    def compile_parameter_list(self):
        if self.tk.peek()[1] == ")":
            return

        _, var_type = self._eat()
        _, var_name = self._eat()
        self.st.define(var_name, var_type, "ARG")

        while self.tk.peek()[1] == ",":
            self._eat(",")
            _, var_type = self._eat()
            _, var_name = self._eat()
            self.st.define(var_name, var_type, "ARG")

    def compile_var_dec(self):
        self._eat("var")
        _, var_type = self._eat()
        _, var_name = self._eat()
        self.st.define(var_name, var_type, "VAR")

        while self.tk.peek()[1] == ",":
            self._eat(",")
            _, var_name = self._eat()
            self.st.define(var_name, var_type, "VAR")

        self._eat(";")

    # -------------------------------------------------------------------------
    # Statements
    # -------------------------------------------------------------------------
    def compile_statements(self):
        while True:
            _, val = self.tk.peek()
            if val == "let":
                self.compile_let()
            elif val == "if":
                self.compile_if()
            elif val == "while":
                self.compile_while()
            elif val == "do":
                self.compile_do()
            elif val == "return":
                self.compile_return()
            else:
                break

    def compile_let(self):
        self._eat("let")
        _, var_name = self._eat()
        seg = self.st.segment_of(var_name)
        idx = self.st.index_of(var_name)

        is_array = self.tk.peek()[1] == "["
        if is_array:
            # 計算目標位址 (base + offset) 並暫存在堆疊上，以支援巢狀陣列運算
            self.vm.write_push(seg, idx)
            self._eat("[")
            self.compile_expression()
            self._eat("]")
            self.vm.write_arithmetic("add")

        self._eat("=")
        self.compile_expression()
        self._eat(";")

        if is_array:
            self.vm.write_pop("temp", 0)     # 暫存右式結果
            self.vm.write_pop("pointer", 1)  # 設定 THAT = 目標位址
            self.vm.write_push("temp", 0)    # 取回右式結果
            self.vm.write_pop("that", 0)     # 寫入 *(base + offset)
        else:
            self.vm.write_pop(seg, idx)

    def compile_if(self):
        else_label = self._new_label("IF_ELSE")
        end_label = self._new_label("IF_END")

        self._eat("if")
        self._eat("(")
        self.compile_expression()
        self._eat(")")

        self.vm.write_arithmetic("not")
        self.vm.write_if(else_label)

        self._eat("{")
        self.compile_statements()
        self._eat("}")

        if self.tk.peek()[1] == "else":
            self.vm.write_goto(end_label)
            self.vm.write_label(else_label)
            self._eat("else")
            self._eat("{")
            self.compile_statements()
            self._eat("}")
            self.vm.write_label(end_label)
        else:
            self.vm.write_label(else_label)

    def compile_while(self):
        exp_label = self._new_label("WHILE_EXP")
        end_label = self._new_label("WHILE_END")

        self._eat("while")
        self.vm.write_label(exp_label)
        self._eat("(")
        self.compile_expression()
        self._eat(")")

        self.vm.write_arithmetic("not")
        self.vm.write_if(end_label)

        self._eat("{")
        self.compile_statements()
        self._eat("}")

        self.vm.write_goto(exp_label)
        self.vm.write_label(end_label)

    def compile_do(self):
        self._eat("do")
        self._compile_subroutine_call()
        self._eat(";")
        self.vm.write_pop("temp", 0)  # 丟棄 void 副程式的回傳值

    def compile_return(self):
        self._eat("return")
        if self.tk.peek()[1] == ";":
            self.vm.write_push("constant", 0)
        else:
            self.compile_expression()
        self._eat(";")
        self.vm.write_return()

    # -------------------------------------------------------------------------
    # Expressions
    # -------------------------------------------------------------------------
    def compile_expression(self):
        self.compile_term()

        while self.tk.peek()[1] in ("+", "-", "*", "/", "&", "|", "<", ">", "="):
            _, op = self._eat()
            self.compile_term()
            if op == "*":
                self.vm.write_call("Math.multiply", 2)
            elif op == "/":
                self.vm.write_call("Math.divide", 2)
            else:
                self.vm.write_arithmetic(self.BINARY_OPS[op])

    def compile_term(self):
        ttype, val = self.tk.peek()

        if ttype == TokenType.INT_CONST:
            self._eat()
            self.vm.write_push("constant", val)

        elif ttype == TokenType.STRING_CONST:
            self._eat()
            self.vm.write_push("constant", len(val))
            self.vm.write_call("String.new", 1)
            for ch in val:
                self.vm.write_push("constant", ord(ch))
                self.vm.write_call("String.appendChar", 2)

        elif ttype == TokenType.KEYWORD:
            self._eat()
            if val == "true":
                self.vm.write_push("constant", 0)
                self.vm.write_arithmetic("not")
            elif val in ("false", "null"):
                self.vm.write_push("constant", 0)
            elif val == "this":
                self.vm.write_push("pointer", 0)
            else:
                raise SyntaxError(f"Unexpected keyword constant: {val}")

        elif val == "(":
            self._eat("(")
            self.compile_expression()
            self._eat(")")

        elif val in self.UNARY_OPS:
            _, op = self._eat()
            self.compile_term()
            self.vm.write_arithmetic(self.UNARY_OPS[op])

        elif ttype == TokenType.IDENTIFIER:
            _, next_val = self.tk.peek(1)
            if next_val == "[":
                _, var_name = self._eat()
                self.vm.write_push(self.st.segment_of(var_name), self.st.index_of(var_name))
                self._eat("[")
                self.compile_expression()
                self._eat("]")
                self.vm.write_arithmetic("add")
                self.vm.write_pop("pointer", 1)
                self.vm.write_push("that", 0)
            elif next_val in ("(", "."):
                self._compile_subroutine_call()
            else:
                _, var_name = self._eat()
                self.vm.write_push(self.st.segment_of(var_name), self.st.index_of(var_name))
        else:
            raise SyntaxError(f"Unexpected token in term: {ttype}, {val}")

    def _compile_subroutine_call(self):
        _, first_name = self._eat()
        n_args = 0

        if self.tk.peek()[1] == ".":
            self._eat(".")
            _, sub_name = self._eat()
            var_type = self.st.type_of(first_name)
            if var_type is not None:
                # 呼叫物件的 method：先推入該物件參考作為 arg 0
                self.vm.write_push(self.st.segment_of(first_name), self.st.index_of(first_name))
                full_name = f"{var_type}.{sub_name}"
                n_args = 1
            else:
                # 呼叫類別的 function 或 constructor
                full_name = f"{first_name}.{sub_name}"
        else:
            # 呼叫同類別內的 method：推入 this (pointer 0) 作為 arg 0
            self.vm.write_push("pointer", 0)
            full_name = f"{self.class_name}.{first_name}"
            n_args = 1

        self._eat("(")
        n_args += self.compile_expression_list()
        self._eat(")")
        self.vm.write_call(full_name, n_args)

    def compile_expression_list(self) -> int:
        count = 0
        if self.tk.peek()[1] == ")":
            return count

        self.compile_expression()
        count += 1
        while self.tk.peek()[1] == ",":
            self._eat(",")
            self.compile_expression()
            count += 1
        return count


# =============================================================================
# 5. Main Entry Point
# =============================================================================
def compile_file(jack_path: str):
    vm_path = os.path.splitext(jack_path)[0] + ".vm"
    tokenizer = JackTokenizer(jack_path)
    writer = VMWriter(vm_path)
    try:
        engine = CompilationEngine(tokenizer, writer)
        engine.compile_class()
    finally:
        writer.close()
    print(f"Compiled: {jack_path} -> {vm_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 JackCompiler.py <file.jack | directory>")
        sys.exit(1)

    target = sys.argv[1]
    if os.path.isdir(target):
        jack_files = [
            os.path.join(target, f)
            for f in sorted(os.listdir(target))
            if f.endswith(".jack")
        ]
        if not jack_files:
            print(f"No .jack files found in {target}")
            sys.exit(1)
        for jf in jack_files:
            compile_file(jf)
    elif os.path.isfile(target) and target.endswith(".jack"):
        compile_file(target)
    else:
        print(f"Invalid input: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()