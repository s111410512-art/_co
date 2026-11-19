# Nand2tetris VM Translator

這是一個基於 Python 實作的 Nand2tetris 虛擬機翻譯器（VM Translator），對應課程的第 7 章與第 8 章。
本程式能夠將 Nand2tetris 的中間碼（`.vm` 檔案）編譯為 Hack 組合語言（`.asm` 檔案），以便在 Hack 硬體架構（或 CPUEmulator）上執行。

## 💡 功能特色 (Features)

本翻譯器完整實作了以下 VM 指令集：

*   **算術與邏輯指令 (Arithmetic & Logical)**
    *   `add`, `sub`, `neg`
    *   `eq`, `gt`, `lt`
    *   `and`, `or`, `not`
*   **記憶體存取指令 (Memory Access)**
    *   `push` / `pop`
    *   支援所有記憶體區段：`argument`, `local`, `static`, `constant` (僅 push), `this`, `that`, `pointer`, `temp`
*   **程式流程控制 (Program Flow)**
    *   `label` (標記)
    *   `goto` (無條件跳轉)
    *   `if-goto` (條件跳轉)
*   **函式呼叫 (Function Calling)**
    *   `function` (宣告函式與區域變數)
    *   `call` (呼叫函式並處理堆疊狀態保存)
    *   `return` (返回呼叫端並恢復堆疊狀態)

## 🚀 系統需求 (Prerequisites)

*   Python 3.x 或以上版本

## 🛠️ 使用方式 (Usage)

本程式支援「**單一檔案**」與「**資料夾**」兩種編譯模式。打開終端機 (Terminal)，輸入以下指令執行：

### 1. 編譯單一檔案 (第 7 章測試)
適用於不包含函式呼叫或不需要初始化 Bootstrap 程式碼的獨立測試檔。

```bash
python VMTranslator.py SimpleAdd.vm
```
*   **輸出**：會在相同目錄下生成 `SimpleAdd.asm`。
*   **注意**：此模式**不會**加入 `Sys.init` 等開機啟動碼。

### 2. 編譯整個資料夾 (第 8 章測試)
當專案包含多個 `.vm` 檔案（例如包含 `Sys.vm` 與其他類別），請將整個資料夾路徑傳入。

```bash
python VMTranslator.py ./FibonacciElement/
```
*   **執行流程**：
    1. 程式會自動加入 Bootstrap 開機碼（將 `SP` 設為 `256` 並呼叫 `Sys.init`）。
    2. 將資料夾內所有的 `.vm` 檔案編譯並合併。
*   **輸出**：會在該資料夾下生成與資料夾同名的組合語言檔，例如 `FibonacciElement.asm`。

## 🧪 測試與驗證 (Testing)

產生的 `.asm` 檔案可以使用 Nand2tetris 官方提供的 **CPUEmulator** 進行驗證：
1. 開啟 `CPUEmulator` 工具。
2. 點擊 `Load ROM` 載入產生的 `.asm` 檔。
3. 點擊 `Load Script` 載入官方對應的測試腳本（`.tst` 檔）。
4. 調整速度並執行，檢查是否順利出現 "End of script - Comparison ended successfully" 的成功訊息。

## 📁 專案架構說明

*   `VMTranslator.py`: 主程式，包含 `Parser`（負責解析 VM 語法）與 `CodeWriter`（負責將解析結果轉譯為 Hack Assembly）兩個主要類別。