
import os
import argparse
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
#api_key = os.getenv("OPENAI_API_KEY")
def generate_test_cases(image_path, prompt):
    """
    Sends an image to OpenAI and saves the response.

    Args:
        image_path (str): The path to the image file.
        prompt (str): The prompt to send to OpenAI.
    """
    # Get the OpenAI API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    client = OpenAI(api_key=api_key)

    # Encode the image in base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
        )

        # Create the output directory
        output_dir = "Generated_Test_Cases"
        os.makedirs(output_dir, exist_ok=True)

        # Save the response
        test_case_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_test_cases.txt")
        with open(test_case_path, "w", encoding="utf-8") as f:
            f.write(response.choices[0].message.content)
        print(f"Test cases saved to {test_case_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    image_name = 'x_screenshot.png'
    prompt = """
            Generate a set of UI tests for the given website using the screenshot provided. The generated test cases should describe the function that it is testing and how it would test it."
            """
    image_path = os.path.join("scraped_data", image_name)

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
    else:
        generate_test_cases(image_path, prompt)
