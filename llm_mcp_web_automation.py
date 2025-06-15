"""
Interactive LLM-Driven Persona & Task Generation System
======================================================

User creates custom personas → LLM generates shopping tasks → Automated execution
"""

import time
import json
import random
import re
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    SELENIUM_AVAILABLE = True
except ImportError:
    print("⚠️ Install selenium: pip install selenium")
    SELENIUM_AVAILABLE = False

# OpenAI imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("⚠️ OpenAI not available - using rule-based decisions")
    OPENAI_AVAILABLE = False


# ===========================================
# CORE CONFIGURATION
# ===========================================

class PersonaType(Enum):
    BEAUTY_ENTHUSIAST = "beauty_enthusiast"
    BUDGET_SHOPPER = "budget_shopper"
    INDECISIVE_SHOPPER = "indecisive_shopper"
    LUXURY_BUYER = "luxury_buyer"
    GIFT_SHOPPER = "gift_shopper"
    SKINCARE_FOCUSED = "skincare_focused"
    CUSTOM = "custom"

class EmotionalState(Enum):
    EXCITED = "excited"
    CURIOUS = "curious"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"

@dataclass
class CustomPersona:
    """Represents a user-created shopping persona with specific traits and preferences."""
    name: str
    type: PersonaType
    budget_range: tuple
    personality_traits: List[str]
    interests: List[str]
    shopping_goals: List[str]
    decision_style: str
    time_preference: str

@dataclass
class LLMTask:
    """Represents an LLM-generated shopping task with expected automation functions."""
    task_name: str
    description: str
    expected_functions: List[str]
    success_criteria: str
    emotional_journey: List[str]

@dataclass
class AutomationStep:
    """Represents a single automation step with reasoning and emotional context."""
    function_name: str
    reasoning: str
    emotional_state: EmotionalState
    parameters: Dict[str, Any] = None


# ===========================================
# VERIFIED SELECTORS
# ===========================================

class TiraSelectors:
    """Verified working selectors for Tira Beauty automation."""
    
    SEARCH_INPUT = "//input[@id='search']"
    CART_ICON = "//img[@title='Cart']"
    
    PRODUCT_CARDS = "//div[@class='product-name']/.."
    PRODUCT_NAMES = "//div[@class='product-name']"
    PRODUCT_PRICES = "//p[@class='discount-price']"
    ADD_TO_BAG_HOVER = "//button[@class='add-to-bag__btn']"
    
    PRODUCT_NAME_DETAIL = "//h1[@id='item_name']"
    ADD_TO_BAG_DETAIL = "(//button[@class='custom-btn primary lg no-tap-highlight'])[1]"
    
    CART_ITEMS = "//div[@class='bag']"
    REMOVE_BUTTON = "//div[@class='left']//button[1]"
    CART_URL = "https://www.tirabeauty.com/cart/bag"


# ===========================================
# SELENIUM FUNCTION CATALOG
# ===========================================

class SeleniumFunctions:
    """Catalog of available Selenium functions for LLM selection."""
    
    @staticmethod
    def get_catalog():
        """Returns complete catalog of automation functions with metadata."""
        return {
            "search_products": {
                "description": "Search for products with persona-specific typing behavior",
                "use_case": "Finding products, starting shopping journey",
                "parameters": {"search_term": "string"},
                "success_rate": "100%",
                "persona_impact": "High"
            },
            "extract_products": {
                "description": "Extract all visible products with names and prices",
                "use_case": "Analyzing available products on current page",
                "success_rate": "100%",
                "persona_impact": "Low"
            },
            "hover_add_to_cart": {
                "description": "Add product to cart using hover interaction",
                "use_case": "Quick impulsive purchase from search results",
                "parameters": {"product_index": "int (0-5)"},
                "success_rate": "100%",
                "persona_impact": "High"
            },
            "click_product_details": {
                "description": "Click product to examine details with tab handling",
                "use_case": "Careful examination before purchase",
                "parameters": {"product_index": "int (0-5)"},
                "success_rate": "100%",
                "persona_impact": "High"
            },
            "add_from_details": {
                "description": "Add to cart from product detail page",
                "use_case": "Purchase after detailed examination",
                "success_rate": "100%",
                "persona_impact": "Medium"
            },
            "view_cart": {
                "description": "Check shopping cart contents and total",
                "use_case": "Reviewing purchases, budget checking",
                "success_rate": "100%",
                "persona_impact": "High"
            },
            "remove_from_cart": {
                "description": "Remove item from cart",
                "use_case": "Changing mind, budget concerns",
                "success_rate": "95%",
                "persona_impact": "High"
            },
            "complete_session": {
                "description": "Finish shopping session with satisfaction",
                "use_case": "When shopping goals are met",
                "success_rate": "100%",
                "persona_impact": "Medium"
            }
        }


# ===========================================
# PERSONA CREATION INTERFACE
# ===========================================

class PersonaCreator:
    """Handles interactive persona creation from user input."""
    
    @staticmethod
    def create_custom_persona():
        """Guides user through step-by-step persona creation process."""
        print("\n🎭 CREATE YOUR CUSTOM SHOPPING PERSONA")
        print("="*50)
        
        name = input("👤 Persona name: ").strip() or "CustomShopper"
        
        print("\n🧠 Select personality traits (separate with commas):")
        print("   Examples: impulsive, careful, analytical, trendy, budget-conscious")
        traits_input = input("🎯 Personality traits: ").strip()
        traits = [t.strip() for t in traits_input.split(",")] if traits_input else ["curious", "practical"]
        
        print("\n💰 Budget range:")
        try:
            min_budget = int(input("   Minimum budget (₹): ") or "500")
            max_budget = int(input("   Maximum budget (₹): ") or "5000")
        except ValueError:
            min_budget, max_budget = 500, 5000
        
        print("\n🎯 Shopping interests (separate with commas):")
        print("   Examples: makeup, skincare, luxury brands, trending products")
        interests_input = input("🛍️ Interests: ").strip()
        interests = [i.strip() for i in interests_input.split(",")] if interests_input else ["beauty products"]
        
        print("\n🎪 Shopping goals for this session (separate with commas):")
        print("   Examples: find birthday gift, restock essentials, try new brands")
        goals_input = input("🎯 Goals: ").strip()
        goals = [g.strip() for g in goals_input.split(",")] if goals_input else ["explore products"]
        
        print("\n🤔 Decision making style:")
        print("   1. Quick and impulsive")
        print("   2. Research-heavy and careful")
        print("   3. Price-focused and practical")
        print("   4. Quality-focused and thorough")
        print("   5. Indecisive and changeable")
        decision_choice = input("Choose (1-5): ").strip()
        
        decision_styles = {
            "1": "quick_impulsive",
            "2": "research_heavy", 
            "3": "price_focused",
            "4": "quality_focused",
            "5": "indecisive"
        }
        decision_style = decision_styles.get(decision_choice, "balanced")
        
        print("\n⏰ Shopping time preference:")
        print("   1. Quick shopping (5-10 minutes)")
        print("   2. Normal browsing (10-15 minutes)")
        print("   3. Extended exploration (15+ minutes)")
        time_choice = input("Choose (1-3): ").strip()
        
        time_prefs = {"1": "quick", "2": "normal", "3": "extended"}
        time_preference = time_prefs.get(time_choice, "normal")
        
        persona_type = PersonaCreator._determine_persona_type(traits, decision_style)
        
        persona = CustomPersona(
            name=name,
            type=persona_type,
            budget_range=(min_budget, max_budget),
            personality_traits=traits,
            interests=interests,
            shopping_goals=goals,
            decision_style=decision_style,
            time_preference=time_preference
        )
        
        print(f"\n✅ PERSONA CREATED: {persona.name}")
        print(f"🎭 Type: {persona.type.value}")
        print(f"🧠 Traits: {', '.join(persona.personality_traits)}")
        print(f"💰 Budget: ₹{persona.budget_range[0]}-{persona.budget_range[1]}")
        print(f"🎯 Goals: {', '.join(persona.shopping_goals)}")
        print(f"⚡ Style: {persona.decision_style}")
        
        return persona
    
    @staticmethod
    def _determine_persona_type(traits, decision_style):
        """Automatically classifies persona type based on traits and decision style."""
        trait_text = " ".join(traits).lower()
        
        if any(word in trait_text for word in ["budget", "cheap", "affordable", "price"]):
            return PersonaType.BUDGET_SHOPPER
        elif any(word in trait_text for word in ["luxury", "premium", "high-end", "quality"]):
            return PersonaType.LUXURY_BUYER
        elif any(word in trait_text for word in ["indecis", "uncertain", "changeable"]):
            return PersonaType.INDECISIVE_SHOPPER
        elif any(word in trait_text for word in ["beauty", "makeup", "trendy", "impulsive"]):
            return PersonaType.BEAUTY_ENTHUSIAST
        elif any(word in trait_text for word in ["skincare", "routine", "organic"]):
            return PersonaType.SKINCARE_FOCUSED
        elif any(word in trait_text for word in ["gift", "birthday", "present"]):
            return PersonaType.GIFT_SHOPPER
        else:
            return PersonaType.CUSTOM


# ===========================================
# LLM TASK GENERATION ENGINE
# ===========================================

class TaskGenerationEngine:
    """Generates intelligent shopping workflows using LLM or rule-based fallback."""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.functions = SeleniumFunctions.get_catalog()
    
    def generate_shopping_tasks(self, persona: CustomPersona) -> List[LLMTask]:
        """Creates complete shopping workflow tailored to persona characteristics."""
        if self.openai_client and OPENAI_AVAILABLE:
            return self._llm_generate_tasks(persona)
        else:
            return self._rule_generate_tasks(persona)
    
    def _llm_generate_tasks(self, persona: CustomPersona) -> List[LLMTask]:
        """Uses LLM to create intelligent, persona-specific shopping tasks."""
        function_list = [f"• {name}: {info['description']}" for name, info in self.functions.items()]
        
        prompt = f"""Create 2-3 realistic shopping tasks for this persona:

PERSONA: {persona.name}
- Budget: ₹{persona.budget_range[0]}-{persona.budget_range[1]}
- Traits: {', '.join(persona.personality_traits)}
- Interests: {', '.join(persona.interests)}
- Goals: {', '.join(persona.shopping_goals)}
- Style: {persona.decision_style}

AVAILABLE FUNCTIONS:
{chr(10).join(function_list)}

Return JSON:
{{
    "tasks": [
        {{
            "task_name": "descriptive name",
            "description": "what persona wants to accomplish",
            "expected_functions": ["function1", "function2"],
            "success_criteria": "how to measure success",
            "emotional_journey": ["emotion1", "emotion2"]
        }}
    ]
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Create realistic shopping tasks. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            response_text = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                tasks = []
                
                for task_data in data.get('tasks', []):
                    task = LLMTask(
                        task_name=task_data.get('task_name', 'Shopping Task'),
                        description=task_data.get('description', 'Complete shopping goal'),
                        expected_functions=task_data.get('expected_functions', ['search_products']),
                        success_criteria=task_data.get('success_criteria', 'Task completed'),
                        emotional_journey=task_data.get('emotional_journey', ['curious'])
                    )
                    tasks.append(task)
                
                return tasks
            
        except Exception as e:
            print(f"⚠️ LLM task generation failed: {e}")
        
        return self._rule_generate_tasks(persona)
    
    def _rule_generate_tasks(self, persona: CustomPersona) -> List[LLMTask]:
        """Fallback rule-based task generation when LLM unavailable."""
        tasks = []
        
        if persona.decision_style == "quick_impulsive":
            tasks.append(LLMTask(
                task_name="Quick Product Discovery",
                description=f"Find and quickly purchase {persona.interests[0]} items",
                expected_functions=["search_products", "extract_products", "hover_add_to_cart"],
                success_criteria="At least 1 item added to cart",
                emotional_journey=["excited", "satisfied"]
            ))
        else:
            tasks.append(LLMTask(
                task_name="Careful Product Research",
                description=f"Research {persona.interests[0]} options thoroughly",
                expected_functions=["search_products", "extract_products", "click_product_details"],
                success_criteria="Product details examined",
                emotional_journey=["curious", "confident"]
            ))
        
        if "budget" in " ".join(persona.personality_traits).lower():
            tasks.append(LLMTask(
                task_name="Budget-Conscious Shopping",
                description="Find affordable options within budget constraints",
                expected_functions=["search_products", "view_cart"],
                success_criteria="Stay within budget limits",
                emotional_journey=["cautious", "satisfied"]
            ))
        
        return tasks


# ===========================================
# ENHANCED AUTOMATION ENGINE
# ===========================================

class TiraAutomation:
    """Handles all Selenium automation with persona-aware behavior."""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.current_products = []
        self.stats = {'actions': 0, 'success': 0, 'cart_items': 0}
        
    def setup_browser(self):
        """Initializes Chrome browser with optimal settings for automation."""
        options = Options()
        options.add_argument("--window-size=1400,1000")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
        self.driver.get("https://www.tirabeauty.com/")
        time.sleep(3)
        print("🔧 Browser ready")
    
    def search_products(self, persona: CustomPersona, search_term: str):
        """Performs product search with persona-specific typing behavior and reactions."""
        print(f"🔍 {persona.name} searching: '{search_term}'")
        try:
            search_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, TiraSelectors.SEARCH_INPUT)))
            search_input.clear()
            
            if persona.decision_style == "quick_impulsive":
                print(f"⚡ {persona.name}: 'Let me quickly find {search_term}!'")
            elif persona.decision_style == "research_heavy":
                print(f"🔍 {persona.name}: 'I need to carefully research {search_term}'")
            elif persona.decision_style == "price_focused":
                print(f"💰 {persona.name}: 'Looking for affordable {search_term}'")
            else:
                print(f"🤔 {persona.name}: 'Hmm, maybe {search_term}?'")
            
            search_input.send_keys(search_term)
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            self._update_stats(True)
            return {'success': True}
        except Exception as e:
            self._update_stats(False)
            return {'success': False, 'error': str(e)}
    
    def extract_products(self, persona: CustomPersona = None):
        """Extracts product information from current page with persona reactions."""
        print("📦 Extracting products...")
        try:
            cards = self.driver.find_elements(By.XPATH, TiraSelectors.PRODUCT_CARDS)
            visible_cards = [c for c in cards if c.is_displayed()][:6]
            
            products = []
            for i, card in enumerate(visible_cards):
                try:
                    name_elem = card.find_element(By.XPATH, ".//div[@class='product-name']")
                    name = name_elem.text.strip()[:50] + "..."
                    
                    price_elem = card.find_element(By.XPATH, ".//p[@class='discount-price']")
                    price_text = price_elem.text.strip()
                    price_match = re.search(r'₹\s*(\d+(?:,\d+)*)', price_text)
                    price = int(price_match.group(1).replace(',', '')) if price_match else 0
                    
                    products.append({'name': name, 'price': price, 'element': card, 'index': i})
                    print(f"  📦 {name} - ₹{price}")
                except:
                    continue
            
            self.current_products = products
            
            if persona and products:
                if persona.decision_style == "price_focused":
                    affordable = [p for p in products if p['price'] <= persona.budget_range[1] * 0.7]
                    print(f"💰 {persona.name}: 'Found {len(affordable)} affordable options!'")
                elif persona.decision_style == "quick_impulsive":
                    print(f"✨ {persona.name}: 'Wow! {len(products)} products to choose from!'")
                else:
                    print(f"🤔 {persona.name}: 'Let me analyze these {len(products)} options...'")
            
            return {'success': True, 'products': products, 'count': len(products)}
            
        except Exception as e:
            return {'success': False, 'products': [], 'count': 0}
    
    def hover_add_to_cart(self, persona: CustomPersona, product_index: int = 0):
        """Adds product to cart using hover interaction with budget checking."""
        print(f"🎭 {persona.name} hover adding product {product_index}")
        try:
            if not self.current_products or product_index >= len(self.current_products):
                return {'success': False, 'error': 'Invalid product index'}
            
            product = self.current_products[product_index]
            
            if product['price'] > persona.budget_range[1]:
                print(f"💸 {persona.name}: 'This is over my budget! ₹{product['price']} > ₹{persona.budget_range[1]}'")
                return {'success': False, 'error': 'Over budget'}
            
            element = product['element']
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
            
            actions = ActionChains(self.driver)
            actions.move_to_element(element).perform()
            time.sleep(2)
            
            add_buttons = self.driver.find_elements(By.XPATH, TiraSelectors.ADD_TO_BAG_HOVER)
            visible_btn = next((btn for btn in add_buttons if btn.is_displayed()), None)
            
            if visible_btn:
                visible_btn.click()
                time.sleep(2)
                
                if persona.decision_style == "quick_impulsive":
                    print(f"🎉 {persona.name}: 'YES! Adding {product['name']} for ₹{product['price']}!'")
                elif persona.decision_style == "price_focused":
                    print(f"💰 {persona.name}: 'Good deal at ₹{product['price']}! Adding to cart.'")
                else:
                    print(f"✅ {persona.name}: 'This looks good, adding to cart.'")
                
                self.stats['cart_items'] += 1
                self._update_stats(True)
                return {'success': True}
            else:
                self._update_stats(False)
                return {'success': False, 'error': 'No add button found'}
                
        except Exception as e:
            self._update_stats(False)
            return {'success': False, 'error': str(e)}
    
    def view_cart(self, persona: CustomPersona):
        """Navigates to cart and displays contents with persona-specific reactions."""
        print(f"🛒 {persona.name} checking cart")
        try:
            self.driver.get(TiraSelectors.CART_URL)
            time.sleep(3)
            
            items = self.driver.find_elements(By.XPATH, TiraSelectors.CART_ITEMS)
            item_count = len(items)
            
            if persona.decision_style == "price_focused":
                if item_count > 0:
                    print(f"💰 {persona.name}: 'Let me check if these {item_count} items fit my budget...'")
                else:
                    print(f"💰 {persona.name}: 'Good, my cart is empty. Staying on budget!'")
            elif persona.decision_style == "indecisive":
                if item_count > 0:
                    print(f"😰 {persona.name}: 'Oh no, I have {item_count} items. Do I really need all these?'")
                else:
                    print(f"😕 {persona.name}: 'My cart is empty... maybe I should add something?'")
            else:
                print(f"😊 {persona.name}: 'I have {item_count} items in my cart!'")
            
            self._update_stats(True)
            return {'success': True, 'item_count': item_count}
            
        except Exception as e:
            self._update_stats(False)
            return {'success': False, 'error': str(e)}
    
    def remove_from_cart(self, persona: CustomPersona):
        """Removes item from cart with persona-appropriate reasoning."""
        print(f"🗑️ {persona.name} removing item")
        try:
            remove_btns = self.driver.find_elements(By.XPATH, TiraSelectors.REMOVE_BUTTON)
            
            if remove_btns:
                if persona.decision_style == "indecisive":
                    print(f"🤔 {persona.name}: 'Actually, I'm not sure I need this... removing it.'")
                elif persona.decision_style == "price_focused":
                    print(f"💰 {persona.name}: 'This is too expensive for my budget. Removing.'")
                else:
                    print(f"🤷 {persona.name}: 'Changed my mind about this one.'")
                
                remove_btns[0].click()
                time.sleep(2)
                
                self.stats['cart_items'] = max(0, self.stats['cart_items'] - 1)
                self._update_stats(True)
                return {'success': True}
            else:
                return {'success': False, 'error': 'No items to remove'}
                
        except Exception as e:
            self._update_stats(False)
            return {'success': False, 'error': str(e)}
    
    def complete_session(self, persona: CustomPersona):
        """Completes shopping session with persona-appropriate satisfaction message."""
        if persona.decision_style == "quick_impulsive":
            print(f"🎉 {persona.name}: 'Great shopping session! Got everything I wanted!'")
        elif persona.decision_style == "price_focused":
            print(f"💰 {persona.name}: 'Perfect! Stayed within budget and found good deals!'")
        elif persona.decision_style == "indecisive":
            print(f"😅 {persona.name}: 'Finally made some decisions. I think I'm done... maybe.'")
        else:
            print(f"😊 {persona.name}: 'Satisfied with my shopping choices!'")
        
        return {'success': True}
    
    def get_context(self):
        """Returns current browser context for LLM decision making."""
        url = self.driver.current_url.lower()
        
        if 'search' in url:
            page_type = 'search_results'
        elif 'product' in url:
            page_type = 'product_details'
        elif 'cart' in url or 'bag' in url:
            page_type = 'cart'
        else:
            page_type = 'homepage'
        
        return {
            'page_type': page_type,
            'products_available': len(self.current_products),
            'cart_items': self.stats['cart_items'],
            'actions_completed': self.stats['actions']
        }
    
    def _update_stats(self, success):
        """Updates internal success statistics for session tracking."""
        self.stats['actions'] += 1
        if success:
            self.stats['success'] += 1
    
    def cleanup(self):
        """Closes browser and cleans up resources."""
        if self.driver:
            self.driver.quit()


# ===========================================
# DEMO ORCHESTRATOR
# ===========================================

class InteractiveDemo:
    """Orchestrates complete demo flow from persona creation to task execution."""
    
    def __init__(self, use_openai=True):
        self.automation = TiraAutomation()
        
        openai_client = None
        if use_openai and OPENAI_AVAILABLE:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                openai_client = OpenAI(api_key=api_key)
                print("🤖 LLM connected for task generation and execution")
        
        self.task_engine = TaskGenerationEngine(openai_client)
    
    def run_interactive_session(self):
        """Executes complete workflow: persona creation → task generation → automation."""
        print("🎭 INTERACTIVE LLM PERSONA & TASK GENERATION DEMO")
        print("="*60)
        print("🔥 User creates persona → LLM generates tasks → AI executes")
        print("="*60)
        
        persona = PersonaCreator.create_custom_persona()
        
        print(f"\n🤖 LLM GENERATING SHOPPING TASKS FOR {persona.name}...")
        tasks = self.task_engine.generate_shopping_tasks(persona)
        
        print(f"\n📋 GENERATED {len(tasks)} TASKS:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task.task_name}")
            print(f"     📝 {task.description}")
            print(f"     🔧 Functions: {', '.join(task.expected_functions)}")
            print(f"     🎯 Success: {task.success_criteria}")
            print(f"     😊 Journey: {' → '.join(task.emotional_journey)}")
        
        input(f"\n⏯️  Press Enter to start {persona.name}'s AI-driven shopping session...")
        
        self.automation.setup_browser()
        
        for i, task in enumerate(tasks, 1):
            print(f"\n{'='*60}")
            print(f"🎯 EXECUTING TASK {i}: {task.task_name}")
            print(f"📝 Goal: {task.description}")
            print(f"{'='*60}")
            
            self._execute_task(task, persona)
            
            if i < len(tasks):
                print(f"🔄 Refreshing browser for next task...")
                self.automation.driver.refresh()
                time.sleep(3)
        
        print(f"\n🎉 ALL TASKS COMPLETED FOR {persona.name}!")
        print(f"📊 Final Stats:")
        print(f"  🎬 Actions: {self.automation.stats['actions']}")
        print(f"  ✅ Success Rate: {(self.automation.stats['success']/max(self.automation.stats['actions'],1)*100):.1f}%")
        print(f"  🛒 Cart Items: {self.automation.stats['cart_items']}")
        
        self.automation.cleanup()
    
    def _execute_task(self, task: LLMTask, persona: CustomPersona):
        """Executes individual task by mapping function names to automation methods."""
        for function_name in task.expected_functions:
            try:
                print(f"\n🔄 Executing: {function_name}")
                
                if function_name == "search_products":
                    search_term = self._get_intelligent_search_term(persona)
                    result = self.automation.search_products(persona, search_term)
                elif function_name == "extract_products":
                    result = self.automation.extract_products(persona)
                elif function_name == "hover_add_to_cart":
                    result = self.automation.hover_add_to_cart(persona, 0)
                elif function_name == "view_cart":
                    result = self.automation.view_cart(persona)
                elif function_name == "remove_from_cart":
                    result = self.automation.remove_from_cart(persona)
                elif function_name == "complete_session":
                    result = self.automation.complete_session(persona)
                    break
                else:
                    continue
                
                if not result.get('success'):
                    print(f"⚠️ Function {function_name} failed: {result.get('error', 'Unknown error')}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Task execution failed: {e}")
                break
    
    def _get_intelligent_search_term(self, persona: CustomPersona):
        """Generates contextually appropriate search terms based on persona attributes."""
        combined_interests = persona.interests + persona.shopping_goals
        
        if persona.decision_style == "price_focused":
            return f"affordable {random.choice(combined_interests)}"
        elif persona.type == PersonaType.LUXURY_BUYER:
            return f"premium {random.choice(combined_interests)}"
        elif "trending" in " ".join(persona.personality_traits).lower():
            return f"trending {random.choice(combined_interests)}"
        else:
            return random.choice(combined_interests)


# ===========================================
# MAIN ENTRY POINT
# ===========================================

def main():
    """Main entry point for interactive LLM-driven automation demo."""
    print("🤖 INTERACTIVE LLM-DRIVEN AUTOMATION SYSTEM")
    print("="*50)
    print("Create custom personas and watch LLM generate + execute tasks!")
    print()
    
    choice = input("🎭 Create custom persona and run demo? (y/n): ").lower()
    
    if choice == 'y':
        demo = InteractiveDemo(use_openai=True)
        demo.run_interactive_session()
    else:
        print("🚀 Interactive system ready when you are!")

if __name__ == "__main__":
    main()