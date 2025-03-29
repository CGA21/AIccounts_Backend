from google import genai
import configparser
import json,ast

def get_api_key():
    config = configparser.ConfigParser()
    config.read('config.ini')  # Make sure the path is correct
    return config['Gemini']['api_key']

def generate_gemini_content(prompt,key):
    client = genai.Client(api_key=key)

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    #print(response.text)
    return ast.literal_eval(response.text.strip().replace("```python", "").replace("```", "").strip())

def create_invoice_dictionary_prompt(extracted_text):
    prompt = f"""
    You are an invoice data extraction and transformation system with dynamic line item categorization.

    Here is the extracted text from an invoice:

    ```{extracted_text}```

    Your task is to convert this text into a Python dictionary.

    The dictionary should have the following keys:
    - 'vendor_name': The name of the vendor.
    - 'invoice_number': The invoice number.
    - 'invoice_date': The date of the invoice (in YYYY-MM-DD format).
    - 'total_amount': The total amount due.
    - 'line_items': A list of dictionaries, where each dictionary represents a line item with the following keys:
        - 'description': The description of the line item.
        - 'amount': The amount of the line item.
        - 'category': A category that best describes the line item, based on the context of the invoice. Determine this category based on the descriptions of the line items.
    - 'address': The address of the vendor.
    - 'payment_terms': Any payment terms listed on the invoice.

    If a key is not present in the extracted text, set the value to 'null'.

    Output the result as a valid Python dictionary, enclosed in triple backticks (```).
    """
    return prompt

def string_to_dict(gemini_output_string):
    """
    Converts a string containing a JSON-like dictionary into a Python dictionary.

    Args:
        gemini_output_string: The string output from Gemini.

    Returns:
        A Python dictionary, or None if conversion fails.
    """
    try:
        # Extract the dictionary from the triple backticks
        start_index = gemini_output_string.find("```") + 3
        end_index = gemini_output_string.rfind("```")
        dictionary_string = gemini_output_string[start_index:end_index].strip()
        result_dict = json.loads(dictionary_string)
        return result_dict
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"Error parsing Gemini's output: {e}")
        print(f"Gemini's raw output: {gemini_output_string}")
        return None  # Or raise an exception if needed

if __name__ == '__main__':
    key = get_api_key()

'''
# Example Usage:
with open('test.txt', 'r') as file:
    extracted_invoice_text = file.read()

prompt = create_invoice_dictionary_prompt(extracted_invoice_text)
generated_text = generate_gemini_content(prompt,key)
print(generated_text)
'''