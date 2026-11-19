import os
import sys


class Parser:
    """負責讀取與解析 .vm 檔案的每一行指令"""

    ARITHMETIC_COMMANDS = {
        "add",
        "sub",
        "neg",
        "eq",
        "gt",
        "lt",
        "and",
        "or",
        "not",
    }

    def __init__(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        self.commands = []
        for line in raw_lines:
            # 移除註解與前後空白
            clean_line = line.split("//")[0].strip()
            if clean_line:
                self.commands.append(clean_line)

        self.current_index = -1
        self.current_command = None

    def has_more_commands(self):
        return self.current_index + 1 < len(self.commands)

    def advance(self):
        self.current_index += 1
        self.current_command = self.commands[self.current_index]

    def command_type(self):
        parts = self.current_command.split()
        cmd = parts[0]
        if cmd in self.ARITHMETIC_COMMANDS:
            return "C_ARITHMETIC"
        elif cmd == "push":
            return "C_PUSH"
        elif cmd == "pop":
            return "C_POP"
        elif cmd == "label":
            return "C_LABEL"
        elif cmd == "goto":
            return "C_GOTO"
        elif cmd == "if-goto":
            return "C_IF"
        elif cmd == "function":
            return "C_FUNCTION"
        elif cmd == "return":
            return "C_RETURN"
        elif cmd == "call":
            return "C_CALL"
        else:
            raise ValueError(f"未知的 VM 指令: {self.current_command}")

    def arg1(self):
        parts = self.current_command.split()
        if self.command_type() == "C_ARITHMETIC":
            return parts[0]
        return parts[1]

    def arg2(self):
        parts = self.current_command.split()
        return int(parts[2])


class CodeWriter:
    """負責將解析後的 VM 指令轉譯為 Hack 組合語言"""

    SEGMENT_MAP = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self, output_path):
        self.file = open(output_path, "w", encoding="utf-8")
        self.file_name = ""
        self.current_function = ""
        self.label_counter = 0

    def set_file_name(self, file_name):
        self.file_name = os.path.splitext(os.path.basename(file_name))[0]

    def write_lines(self, lines):
        self.file.write("\n".join(lines) + "\n")

    def write_init(self):
        """寫入 Bootstrap 開機初始化程式碼 (SP=256, call Sys.init)"""
        self.write_lines(["// Bootstrap code", "@256", "D=A", "@SP", "M=D"])
        self.write_call("Sys.init", 0)

    def write_arithmetic(self, command):
        self.write_lines([f"// {command}"])
        if command in {"add", "sub", "and", "or"}:
            op = {"add": "+", "sub": "-", "and": "&", "or": "|"}[command]
            self.write_lines([
                "@SP",
                "AM=M-1",  # SP--, A = SP
                "D=M",  # D = y
                "A=A-1",  # A = SP - 1 (指向 x)
                f"M=M{op}D",  # x = x op y
            ])
        elif command in {"neg", "not"}:
            op = "-" if command == "neg" else "!"
            self.write_lines(["@SP", "A=M-1", f"M={op}M"])
        elif command in {"eq", "gt", "lt"}:
            jmp = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
            true_label = f"TRUE_{self.label_counter}"
            end_label = f"END_{self.label_counter}"
            self.label_counter += 1
            self.write_lines([
                "@SP",
                "AM=M-1",
                "D=M",  # D = y
                "A=A-1",
                "D=M-D",  # D = x - y
                f"@{true_label}",
                f"D;{jmp}",
                "@SP",
                "A=M-1",
                "M=0",  # False (0)
                f"@{end_label}",
                "0;JMP",
                f"({true_label})",
                "@SP",
                "A=M-1",
                "M=-1",  # True (-1)
                f"({end_label})",
            ])

    def write_push_pop(self, cmd_type, segment, index):
        self.write_lines([f"// {cmd_type} {segment} {index}"])
        if cmd_type == "C_PUSH":
            if segment == "constant":
                self.write_lines([f"@{index}", "D=A"])
            elif segment in self.SEGMENT_MAP:
                base = self.SEGMENT_MAP[segment]
                self.write_lines(
                    [f"@{base}", "D=M", f"@{index}", "A=D+A", "D=M"]
                )
            elif segment == "temp":
                self.write_lines([f"@{5 + index}", "D=M"])
            elif segment == "pointer":
                target = "THIS" if index == 0 else "THAT"
                self.write_lines([f"@{target}", "D=M"])
            elif segment == "static":
                self.write_lines([f"@{self.file_name}.{index}", "D=M"])

            # 將 D 推入堆疊頂端並將 SP + 1
            self.write_lines(["@SP", "A=M", "M=D", "@SP", "M=M+1"])

        elif cmd_type == "C_POP":
            if segment in self.SEGMENT_MAP:
                base = self.SEGMENT_MAP[segment]
                self.write_lines([
                    f"@{base}",
                    "D=M",
                    f"@{index}",
                    "D=D+A",
                    "@R13",  # 暫存目標記憶體位址
                    "M=D",
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "@R13",
                    "A=M",
                    "M=D",
                ])
            elif segment == "temp":
                self.write_lines(
                    ["@SP", "AM=M-1", "D=M", f"@{5 + index}", "M=D"]
                )
            elif segment == "pointer":
                target = "THIS" if index == 0 else "THAT"
                self.write_lines(["@SP", "AM=M-1", "D=M", f"@{target}", "M=D"])
            elif segment == "static":
                self.write_lines([
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    f"@{self.file_name}.{index}",
                    "M=D",
                ])

    def write_label(self, label):
        full_label = (
            f"{self.current_function}${label}"
            if self.current_function
            else label
        )
        self.write_lines([f"// label {label}", f"({full_label})"])

    def write_goto(self, label):
        full_label = (
            f"{self.current_function}${label}"
            if self.current_function
            else label
        )
        self.write_lines([f"// goto {label}", f"@{full_label}", "0;JMP"])

    def write_if(self, label):
        full_label = (
            f"{self.current_function}${label}"
            if self.current_function
            else label
        )
        self.write_lines(
            [f"// if-goto {label}", "@SP", "AM=M-1", "D=M", f"@{full_label}", "D;JNE"]
        )

    def write_function(self, function_name, num_locals):
        self.current_function = function_name
        self.write_lines(
            [f"// function {function_name} {num_locals}", f"({function_name})"]
        )
        # 初始化 num_locals 個區域變數為 0
        for _ in range(num_locals):
            self.write_push_pop("C_PUSH", "constant", 0)

    def write_call(self, function_name, num_args):
        ret_label = f"{function_name}$ret.{self.label_counter}"
        self.label_counter += 1
        self.write_lines([f"// call {function_name} {num_args}"])

        # 1. push returnAddress
        self.write_lines(
            [f"@{ret_label}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
        )
        # 2. push LCL, ARG, THIS, THAT
        for seg in ["LCL", "ARG", "THIS", "THAT"]:
            self.write_lines(
                [f"@{seg}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
            )
        # 3. ARG = SP - 5 - num_args
        self.write_lines([
            "@SP",
            "D=M",
            "@5",
            "D=D-A",
            f"@{num_args}",
            "D=D-A",
            "@ARG",
            "M=D",
        ])
        # 4. LCL = SP
        self.write_lines(["@SP", "D=M", "@LCL", "M=D"])
        # 5. goto function_name & 宣告返回標籤
        self.write_lines([f"@{function_name}", "0;JMP", f"({ret_label})"])

    def write_return(self):
        self.write_lines([
            "// return",
            "@LCL",
            "D=M",
            "@R13",  # R13 = endFrame (LCL)
            "M=D",
            "@5",
            "A=D-A",
            "D=M",
            "@R14",  # R14 = retAddr (*(endFrame - 5))
            "M=D",
            "@SP",
            "AM=M-1",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",  # *ARG = pop() (回傳值放到呼叫端的 ARG 0)
            "@ARG",
            "D=M+1",
            "@SP",
            "M=D",  # SP = ARG + 1
        ])
        # 恢復 THAT, THIS, ARG, LCL
        for offset, seg in enumerate(["THAT", "THIS", "ARG", "LCL"], start=1):
            self.write_lines(
                ["@R13", "D=M", f"@{offset}", "A=D-A", "D=M", f"@{seg}", "M=D"]
            )
        # 跳轉回呼叫端
        self.write_lines(["@R14", "A=M", "0;JMP"])

    def close(self):
        self.file.close()


def translate_file(parser, code_writer):
    while parser.has_more_commands():
        parser.advance()
        ctype = parser.command_type()
        if ctype == "C_ARITHMETIC":
            code_writer.write_arithmetic(parser.arg1())
        elif ctype in {"C_PUSH", "C_POP"}:
            code_writer.write_push_pop(ctype, parser.arg1(), parser.arg2())
        elif ctype == "C_LABEL":
            code_writer.write_label(parser.arg1())
        elif ctype == "C_GOTO":
            code_writer.write_goto(parser.arg1())
        elif ctype == "C_IF":
            code_writer.write_if(parser.arg1())
        elif ctype == "C_FUNCTION":
            code_writer.write_function(parser.arg1(), parser.arg2())
        elif ctype == "C_CALL":
            code_writer.write_call(parser.arg1(), parser.arg2())
        elif ctype == "C_RETURN":
            code_writer.write_return()


def main():
    if len(sys.argv) != 2:
        print("用法: python VMTranslator.py <file.vm | directory>")
        sys.exit(1)

    input_path = sys.argv[1].rstrip("/\\")

    if os.path.isdir(input_path):
        vm_files = [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.endswith(".vm")
        ]
        dir_name = os.path.basename(input_path)
        output_path = os.path.join(input_path, f"{dir_name}.asm")
        is_dir = True
    else:
        vm_files = [input_path]
        output_path = os.path.splitext(input_path)[0] + ".asm"
        is_dir = False

    code_writer = CodeWriter(output_path)

    # 依據課程規範：若編譯整個資料夾，需寫入 Bootstrap 初始化碼
    if is_dir:
        code_writer.write_init()

    for vm_file in vm_files:
        code_writer.set_file_name(vm_file)
        parser = Parser(vm_file)
        translate_file(parser, code_writer)

    code_writer.close()
    print(f"成功產生組合語言檔案: {output_path}")


if __name__ == "__main__":
    main()