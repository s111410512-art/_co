# Nand2Tetris Project 11 — Jack 語言編譯器 (Jack Compiler)

本專案以 Python 實作 **Nand2Tetris Project 11** 的完整 **Jack 語言編譯器**（`JackCompiler.py`），負責將高階物件導向語言 Jack（`.jack`）編譯為 Hack 平台的虛擬機程式碼（`.vm`）。

---

## 目錄結構

```text
hw12/
├── JackCompiler.py      # Jack 編譯器主程式（整合五大核心模組）
├── README.md            # 本專案說明文件
├── Average/             # 測試專案 1：計算輸入數列平均值
│   └── Main.jack
├── ComplexArrays/       # 測試專案 2：巢狀陣列存取與賦值測試
│   └── Main.jack
├── ConvertToBin/        # 測試專案 3：十進位轉二進位運算
│   └── Main.jack
├── Pong/                # 測試專案 4：完整 Pong 乒乓球遊戲
│   ├── Ball.jack
│   ├── Bat.jack
│   ├── Main.jack
│   └── PongGame.jack
├── Seven/               # 測試專案 5：基礎算術運算與輸出
│   └── Main.jack
└── Square/              # 測試專案 6：互動式方塊移動與縮放遊戲
    ├── Main.jack
    ├── Square.jack
    └── SquareGame.jack
```

---

## 系統架構與核心模組

`JackCompiler.py` 依照 Nand2Tetris 標準規格實作了以下五個核心元件：

1. **`JackTokenizer`（詞法分析器）**
   - 使用單次掃描的正則表達式過濾空白、單行註解（`//`）與多行／API 註解（`/* ... */`），避免字串常數內的註解符號遭誤判。
   - 將原始碼切分為五種 Token 類型：`KEYWORD`、`SYMBOL`、`IDENTIFIER`、`INT_CONST`、`STRING_CONST`。

2. **`SymbolTable`（符號表）**
   - 維護**類別層級**（`STATIC`、`FIELD`）與**副程式層級**（`ARG`、`VAR`）雙層作用域。
   - 自動追蹤各類別變數的索引值，並對應至 Hack VM 的記憶體區段（`static`、`this`、`argument`、`local`）。

3. **`VMWriter`（虛擬機程式碼輸出器）**
   - 封裝所有 Hack VM 指令的輸出格式，包括 `push`、`pop`、算術與邏輯運算、`label`、`goto`、`if-goto`、`call`、`function` 及 `return`。

4. **`CompilationEngine`（遞迴下降語法分析與程式碼產生器）**
   - 採用遞迴下降法解析 Jack 語法，並直接轉換為對應的 `.vm` 堆疊指令：
     - **物件與副程式**：`constructor` 透過 `Memory.alloc` 配置記憶體並設定 `pointer 0`（`this`）；`method` 將隱藏的第 0 個參數（`argument 0`）載入 `pointer 0`。
     - **控制流程**：為 `if / else` 與 `while` 動態產生唯一編號的標籤（Label），支援任意深度的巢狀判斷與迴圈。
     - **陣列運算**：支援如 `a[b[i]] = c[j]` 的巢狀陣列賦值，先將目標位址保留於堆疊中，最後透過 `temp 0` 與 `pointer 1`（`that 0`）完成寫入。
     - **字串與乘除法**：自動轉譯為標準作業系統呼叫（`String.new`、`String.appendChar`、`Math.multiply`、`Math.divide`）。

5. **主程式入口（CLI）**
   - 支援傳入單一 `.jack` 檔案或包含多個 `.jack` 檔案的資料夾，並在同目錄下輸出對應的 `.vm` 檔案。

---

## 環境需求與使用方式

### 環境需求
- Python 3.x（僅使用標準函式庫，無須額外安裝套件）

### 編譯單一專案或單一檔案
先切換至 `hw12` 目錄下，再執行編譯指令：

```bash
# 編譯整個資料夾內的所有 .jack 檔案
python JackCompiler.py Seven

# 或編譯單一 .jack 檔案
python JackCompiler.py Seven/Main.jack
```

執行成功後，終端機將顯示類似以下訊息，並在該資料夾中產生對應的 `.vm` 檔案：
```text
Compiled: Seven/Main.jack -> Seven/Main.vm
```

### 一次編譯全部 6 個測試專案

* **Git Bash / macOS / Linux：**
  ```bash
  for dir in Seven ConvertToBin Square Average Pong ComplexArrays; do
      python JackCompiler.py "$dir"
  done
  ```

* **Windows PowerShell：**
  ```powershell
  foreach ($dir in "Seven","ConvertToBin","Square","Average","Pong","ComplexArrays") {
      python JackCompiler.py $dir
  }
  ```

* **Windows 命令提示字元（CMD）：**
  ```cmd
  for %d in (Seven ConvertToBin Square Average Pong ComplexArrays) do python JackCompiler.py %d
  ```

---

## 測試與驗證方式

編譯產生 `.vm` 檔案後，可透過 Nand2Tetris 官方提供的 **VM Emulator** 進行驗證：

1. 開啟 **VM Emulator**（本機版或線上 Web IDE）。
2. 點選 **Load Program**，選擇要測試的專案資料夾（例如 `hw12/Seven`）。
3. 將執行模式切換為 **No animation**（以獲得正常執行速度）。
4. 點擊 **Run** 開始執行，並確認輸出結果符合預期：

| 測試專案 | 預期執行結果 |
| :--- | :--- |
| **Seven** | 螢幕印出計算結果 `7`。 |
| **ConvertToBin** | 將 RAM[8000] 的數值轉換為二進位並存入 RAM[8001]～RAM[8016]（可搭配對應測試腳本檢驗）。 |
| **Square** | 螢幕左上角出現黑色方塊，可使用方向鍵移動，按 `z`/`x` 縮放，按 `q` 結束。 |
| **Average** | 依螢幕提示輸入數字個數與數值後，正確印出平均值。 |
| **Pong** | 啟動可遊玩的乒乓球遊戲，使用左右方向鍵控制球拍反彈球並計分。 |
| **ComplexArrays** | 螢幕依序印出各組複雜陣列運算的預期結果與實際結果，兩者須完全一致。 |