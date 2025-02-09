from google.cloud import translate_v2 as translate
import os

# Set the path to your service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\naman\\Downloads\\watchful-slice-443014-f0-ecd3668e9487.json"

def translate_text():
    """Prompt user for text and translate to the target language."""
    try:
        # Initialize the client
        client = translate.Client()

        # Get user input for text and target language
        text = input("Enter the text to translate: ")
        target_language = input("Enter the target language code (e.g., 'es' for Spanish, 'fr' for French): ")

        # Translate the text
        result = client.translate(text, target_language=target_language)

        # Display the translation result
        print("\nTranslation Successful!")
        print(f"Original Text: {text}")
        print(f"Translated Text: {result['translatedText']}")
    except Exception as e:
        print("Error occurred:", e)

if __name__ == "__main__":
    translate_text()