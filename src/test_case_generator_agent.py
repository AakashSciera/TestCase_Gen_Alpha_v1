# Filename: test_case_generator_agent.py
# Description: A LangChain agent for generating front-end system test cases.
# Author: Gemini Expert Agent
# Date: 2025-09-16

# --- Installation ---
# Before running, ensure you have the required packages installed.
# pip install langchain langchain-openai openai pillow beautifulsoup4

import os
import json
import base64
import generate_tests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

# --- Environment Setup ---
# It's best practice to use environment variables for API keys.
# Create a .env file in your project root with: OPENAI_API_KEY="your_api_key"
# or run: export OPENAI_API_KEY="your_api_key"
# For this script, we will set it directly if not found, but this is not recommended for production.
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE" # IMPORTANT: Replace with your actual key

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from openai import OpenAI

# --- Custom Tool Definitions ---
# These functions are decorated with @tool, turning them into tools the LangChain agent can use.

@tool
def analyze_screenshot(image_path: str) -> str:
    """
    Analyzes a screenshot of a website's UI and returns a JSON object
    containing observable features and initial, high-level test cases.
    This simulates a multimodal model's analysis of the UI.
    """
    print(f"\n[Tool Call] > Analyzing screenshot: {image_path}")
    # In a real implementation, this would involve a call to a multimodal LLM
    # or an image analysis service. For this script, we return a mock response.
    if not os.path.exists(image_path):
        return json.dumps({"error": "Screenshot file not found."})
    prompt = "Inputs:known_url: \"https://x.com\"\n  - device_hint: \"DESKTOP\"\n  - notes: \"Focus on all the actionable elements.\"\nObjective: Produce a structured test plan."
    llm_response = generate_tests.generate_test_cases(image_path, prompt)
    return llm_response
    #return json.dumps(mock_response)

@tool
def analyze_dom(dom_content) -> str:
    """
    Analyzes the HTML DOM of a website to extract detailed information about
    interactive elements, forms, and their attributes. Returns a JSON object
    with detailed testable features.
    """
    print("\n[Tool Call] > Analyzing DOM content...")
    
    soup = BeautifulSoup(dom_content, 'html.parser')
    interactive_elements = []
    detailed_test_cases = []
    
    # Find all buttons, links, inputs, textareas, and selects
    for element in soup.find_all(['button', 'a', 'input', 'textarea', 'select']):
        element_info = {
            "tag": element.name,
            "text": element.get_text(strip=True),
            "attributes": element.attrs
        }
        interactive_elements.append(element_info)
        
        # Generate test cases based on element type
        element_id = element.get('id', '')
        element_text = element.get_text(strip=True)
        
        if element.name == 'button':
            test_case = f"Verify that the '{element_text}' button"
            if element_id:
                test_case += f" (id: {element_id})"
            test_case += " is clickable and triggers the expected action."
            detailed_test_cases.append(test_case)
            
        elif element.name == 'a':
            href = element.get('href', '#')
            test_case = f"Verify that the '{element_text}' link"
            if element_id:
                test_case += f" (id: {element_id})"
            test_case += f" navigates to '{href}'."
            detailed_test_cases.append(test_case)
            
        elif element.name == 'input':
            input_type = element.get('type', 'text')
            placeholder = element.get('placeholder', '')
            test_case = f"Verify that the input field"
            if element_id:
                test_case += f" (id: {element_id})"
            if placeholder:
                test_case += f" with placeholder '{placeholder}'"
            test_case += f" accepts '{input_type}' input."
            detailed_test_cases.append(test_case)

        elif element.name == 'textarea':
            placeholder = element.get('placeholder', '')
            test_case = f"Verify that the textarea"
            if element_id:
                test_case += f" (id: {element_id})"
            if placeholder:
                test_case += f" with placeholder '{placeholder}'"
            test_case += " accepts multi-line text input."
            detailed_test_cases.append(test_case)

        elif element.name == 'select':
            test_case = f"Verify that the dropdown/select menu"
            if element_id:
                test_case += f" (id: {element_id})"
            test_case += " allows option selection."
            detailed_test_cases.append(test_case)

    response = {
        "interactive_elements": interactive_elements,
        "detailed_test_cases": detailed_test_cases
    }
    
    print("[Tool Call] > DOM analysis complete.")
    return json.dumps(response, indent=2)

@tool
def evaluate_test_cases(test_plan_json: str, rubric: str) -> str:
    """
    Evaluates a list of generated test cases against a given rubric to determine
    if their quality and coverage are sufficient.
    """
    print("\n[Tool Call] > Evaluating generated test cases...")
    
    try:
        test_plan = json.loads(test_plan_json)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format in the test plan."

    test_case_strings = []
    if "test_areas" in test_plan:
        for area in test_plan["test_areas"]:
            test_case_strings.extend(area.get("test_ideas", []))

    case_str = "\n".join(test_case_strings)
    print(f"--- Cases to Evaluate ---\n{case_str}\n-------------------------")
    
    # Simple logic to check if the cases seem superficial.
    if any("DOM" in case or "id:" in case or "input" in case for case in test_case_strings):
        evaluation = {
            "is_sufficient": True,
            "reason": "The test cases are comprehensive, covering both visual and DOM-based interactions.",
            "score": 9.5
        }
    else:
        evaluation = {
            "is_sufficient": False,
            "reason": "The initial test cases are too high-level and only cover basic visibility. Deeper analysis of the DOM is required to test user interactions.",
            "score": 4.0
        }
    print(f"[Tool Call] > Evaluation result: Sufficient? {evaluation['is_sufficient']}")
    return json.dumps(evaluation)

@tool
def create_pytest_tests(test_plan_json: str) -> str:
    """
    Generates a Python file with a test interface created by an LLM.
    The test plan is the output of the analyze_screenshot tool.
    """
    print("\n[Tool Call] > Generating test interface with LLM...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY environment variable not set."
    client = OpenAI(api_key=api_key)

    prompt = f"""
    Generate a complete Python script that defines a comprehensive test interface based on the following test plan.

    The script should:
    1.  Be a valid Python script.
    2.  Use pytest conventions.
    3.  Contain a separate class for each test area and user flow.
    4.  Contain a separate method for each test idea.
    5.  The methods should have descriptive names based on the test idea.
    6.  The methods should have docstrings that explain the test.
    7.  The body of each method must be `pass`. Do not write any implementation logic.

    Here is the test plan in JSON format:
    {test_plan_json}

    Generate only the Python code for the script, with explanations when necessary.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a senior QA engineer specializing in test automation. Your task is to write a Python script that defines a test interface using pytest."},
            {"role": "user", "content": prompt}
        ]
    )
    generated_code = response.choices[0].message.content

    output_dir = "Generated_Test_Cases"
    os.makedirs(output_dir, exist_ok=True)
    test_file_path = os.path.join(output_dir, "test_interface_llm.py")

    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(generated_code)

    return f"Successfully generated LLM-assisted test interface in {test_file_path}"


def main():
    """
    Main execution block to set up and run the test case generation agent.
    """
    print("--- Initializing Test Case Generation Agent ---")

    # 1. Create a dummy screenshot for the agent to use
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "..", "scraped_data", 'x_screenshot.png')
    screenshot_file = image_path

    # 2. Define sample inputs for the agent
    dom_path = os.path.join(script_dir, "..", "scraped_data", 'x_dom.html')
    with open(dom_path, 'r', encoding='utf-8') as f:
        sample_dom_content = f.read()
    evaluation_rubric = """
    A high-quality test suite should:
    1. Cover all primary user-facing interactive elements (buttons, links, inputs).
    2. Verify not just visibility but also behavior (e.g., clicks, navigation, input handling).
    3. Include assertions for important attributes like placeholders and ARIA labels.
    4. Be derived from both visual layout and underlying DOM structure.
    """

    # 3. Define the tools the agent can use
    tools = [analyze_screenshot, analyze_dom, evaluate_test_cases, create_pytest_tests]

    # 4. Set up the Large Language Model
    # Ensure your OPENAI_API_KEY is set in your environment variables
    llm = ChatOpenAI(model="gpt-4o")

    # 5. Create the prompt template
    # This prompt guides the agent to follow the specific reasoning process.
    # It now includes placeholders for chat history and the agent_scratchpad, which are required.
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert software quality assurance engineer. Your mission is to generate a comprehensive set of system test cases for a website's front-end based on the provided materials.

        You MUST follow this exact sequence of steps:
        1.  Start by calling the `analyze_screenshot` tool with the provided image path to get a visual understanding and a detailed test plan in JSON format.
        2.  Next, you MUST call the `evaluate_test_cases` tool. Use the `generated_test_cases` from the previous step as input and pass the provided rubric to assess their quality.
        3.  Review the result from the evaluation. If the evaluation indicates the test cases are NOT sufficient (`is_sufficient` is false), you MUST then call the `analyze_dom` tool with the provided DOM content to gather more detailed information.
        4.  After gathering all information, call the `create_pytest_tests` tool. Use the JSON test plan from the `analyze_screenshot` tool as the input.
        5.  Finally, synthesize all the information you have gathered (from the screenshot, the DOM, the evaluation feedback, and the pytest generation). Output a summary of the generated tests and the location of the pytest file.

        Begin the process now.
        """),
        # MessagesPlaceholder is for chat history, allowing the agent to be conversational.
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", """
        **Inputs provided to you:**
        - Screenshot Path: {image_path}
        - DOM Content: {dom_content}
        - Evaluation Rubric: {rubric}
        """),
        # The agent_scratchpad is crucial for the agent to store its thoughts and tool outputs.
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 6. Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)

    # 7. Create the Agent Executor to run the agent
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    print("\n--- Starting Agent Execution ---")
    
    # 8. Invoke the agent with the inputs
    # The 'input' dictionary keys must match the variables in the prompt template.
    # We also provide an empty chat_history for the first turn.
    result = agent_executor.invoke({
        "image_path": screenshot_file,
        "dom_content": sample_dom_content,
        "rubric": evaluation_rubric,
        "chat_history": []
    })

    print("\n--- Agent Execution Finished ---")
    
    # 9. Neatly print the final output
    print("\n" + "="*50)
    print("      FINAL GENERATED SYSTEM TEST CASES")
    print("="*50 + "\n")
    # The final answer is in the 'output' key of the result dictionary
    print(result['output'])
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    # Check for API key before running
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "YOUR_API_KEY_HERE":
        print("ERROR: OPENAI_API_KEY is not set.")
        print("Please set it as an environment variable or replace the placeholder in the script.")
    else:
        main()
