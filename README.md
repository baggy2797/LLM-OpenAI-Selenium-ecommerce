# 🤖 LLM-Powered Web Automation with Multi-step Command Parsing (MCP)

This project showcases how to use a **Large Language Model (LLM)** to parse natural language instructions into actionable web automation tasks using Selenium. It mimics how a human would interact with a website—clicking buttons, entering text, and navigating pages—based on plain English commands.

## 🌐 Use Case

> "Search for matte lipstick and add the first product to the cart."

This instruction is parsed by the LLM and executed step-by-step on the [TIRA Beauty](https://www.tirabeauty.com) website or any compatible e-commerce site.

---

## ⚙️ Features

- ✅ Accepts natural language instructions
- ✅ Converts instructions into structured action steps
- ✅ Executes those steps with Selenium WebDriver
- ✅ Persona-driven prompt formatting (e.g., "Shopper", "QA")
- ✅ Modular, extensible design

---

## 🧠 Tech Stack

- Python 3.12+
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- Selenium
- BeautifulSoup (optional DOM parsing)

---
