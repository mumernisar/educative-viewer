import os
import google.generativeai as genai
def query_gemini(prompt):
    try:
        print(os.getenv('GEMINI_API_KEY'))
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response._done != True:
            raise Exception(f"Error querying Gemini: {response.text}")
        
        return response
    except Exception as e:
        print(e , "Exception occured")




