# 第八週報告：IC 設計的 EDA 工具與實作資源解析

**題目**：IC 設計的 EDA 是什麼？  
**課程名稱**：IC 設計基礎與 EDA 工具應用  
**學生姓名**：[吳宥均]  
**學號**：[111410512]  
**日期**：2026年10月29日  

---

## 摘要

本報告旨在探討積體電路（IC）設計領域中「電子設計自動化」（Electronic Design Automation, EDA）的核心概念、在晶片開發流程中的關鍵角色，並結合當前開源 EDA 工具、網頁化模擬環境與國際頂尖大學（如康乃爾大學 ECE 5745）的教學體系進行分析。

---

## 目錄

1. IC 設計與 EDA 概述
2. 現代 IC 設計流程與 EDA 工具鏈
3. 參考專案與開源 EDA 實作分析
4. 康乃爾大學 ECE 5745 課程體系剖析
5. 結論與心得

---

## 一、 IC 設計的 EDA 是什麼？

**EDA（Electronic Design Automation，電子設計自動化）** 是指利用專門的電腦軟體、演算法與硬體平台，輔助工程師進行 IC 晶片之架構設計、邏輯合成、實體佈局、電路模擬與物理驗證的技術系統。

隨著半導體製程進入奈米級世代，單一晶片上可容納數百億個電晶體（例如先進 CPU、GPU 與 AI 晶片）。傳統人工手繪與驗證已完全不可能實現，EDA 因此成為半導體產業鏈的最上游核心支柱，被譽為**「晶片之母」**。

---

## 二、 EDA 在 IC 設計流程中的核心角色

完整的 IC 設計可分為前端（邏輯設計）與後端（實體設計），EDA 工具貫穿其中的每一個步驟：

### 1. 前端設計與驗證（Front-End）
* **硬體描述語言（RTL Coding）**：使用 Verilog、SystemVerilog 或 Veryl 撰寫硬體邏輯。
* **功能模擬（Functional Simulation）**：驗證 RTL 程式碼的功能邏輯是否符合設計規範。
* **邏輯合成（Logic Synthesis）**：將 RTL 轉換為由基本邏輯閘組成的門階網表（Gate-Level Netlist）。

### 2. 後端設計與實體驗證（Back-End）
* **自動佈局與繞線（Place & Route, P&R）**：決定邏輯閘在晶片上的實體位置並完成金屬線連接。
* **靜態時序分析（STA, Static Timing Analysis）**：檢查電路訊號延遲，確保晶片能在指定頻率下正常運作。
* **物理驗證（Physical Verification）**：
  * **DRC（Design Rule Checking）**：檢查佈局是否符合晶圓代工廠的幾何製程規範。
  * **LVS（Layout Versus Schematic）**：核對佈局圖與邏輯電路網表是否完全一致。

---

## 三、 參考專案與開源 EDA 工具實作分析

本報告參考了數個當前開源與輕量化的 EDA 工具發展專案，展現了 EDA 朝向**網頁化（Web-based）**與**高階抽象化**的趨勢：

### 1. AI 自製 EDA / Veryl2Chip
* **專案網址**：https://github.com/ccc-eda/veryl2chip/
* **線上測試**：https://ccc-eda.github.io/veryl2chip/web/dist/index.html
* **分析**：該專案結合了現代化硬體描述語言 **Veryl**（具備現代程式語言語法與安全性，可編譯為標準 Verilog）。透過瀏覽器端的輕量介面，使用者無需配置複雜的 Linux EDA 環境，即可進行硬體程式碼編輯、邏輯合成與模擬驗證。

### 2. Nand2Tetris 網頁版硬體模擬器
* **專案網址**：https://github.com/ccc-js/hack-computer
* **線上測試**：https://ccc-js.github.io/hack-computer/dist/hdl.html
* **分析**：基於知名課程 *Nand2Tetris*（從零建構電腦系統）所打造的 JS 網頁模擬器。透過自訂的 HDL 語法，使用者可以從基礎的 NAND 閘逐步建造出多工器（Mux）、算術邏輯單元（ALU）、中央處理器（CPU）與完整電腦，是理解 EDA 邏輯模擬器（Simulator）運作原理的最佳入門實作。

### 3. 開源 EDA 電子書資源
* **專案網址**：https://github.com/ccc-eda/eda-books/tree/main/book
* **分析**：系統化整理了 EDA 工具開發的核心演算法，如邏輯合成演算法、圖論在佈局繞線中的應用、時序分析模型等，提供了深入理解 EDA 軟體底層結構的理論基石。

---

## 四、 頂尖學府教學體系分析：康乃爾大學 ECE 5745

參考 **Cornell University ECE 5745: Complex Digital ASIC Design** 課程手冊：
* **教學目標**：讓學生熟悉完整的數位 ASIC 設計流程，從高階抽象架構設計一路延伸至晶片下單（Tape-out）。
* **硬體建模語言**：課程採用 **PyMTL**（基於 Python 的硬體描述與驗證框架）與標準 **Verilog**，兼具快速原型驗證與精確硬體控制。
* **PPA 優化**：強調在 EDA 工具輔助下，針對晶片之**功耗（Power）、效能（Performance）與面積（Area）**進行綜合折衷與優化。

---

## 五、 結論與心得

EDA 不僅是 IC 工程師的輔助軟體，其本身集成了計算幾何、圖論、布林可滿足性（SAT）與編譯器原理等多學科技術。透過如 Veryl2Chip 與 Hack-Computer 等開源網頁化工具，大幅降低了學習 IC 設計與 EDA 運作邏輯的門檻，讓學習者能清晰理解從「高階程式碼」轉化為「實體矽晶片」的全過程。

---

## 參考資料

1. **Veryl2Chip 專案**：https://github.com/ccc-eda/veryl2chip/
2. **Hack Computer 網頁模擬器**：https://github.com/ccc-js/hack-computer
3. **EDA 電子書**：https://github.com/ccc-eda/eda-books/tree/main/book
4. **Cornell ECE 5745 課程手冊**：https://www.csl.cornell.edu/courses/ece5745/handouts.html