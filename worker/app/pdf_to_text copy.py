from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult
import os 

# endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "https://docintel9784.cognitiveservices.azure.com/")
# key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "b0f90ee2ddf84d3d8532865d29fa0ca0")

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

with open("resume.pdf", "rb") as f:
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-read",
        body=f,
        output=[AnalyzeOutputOption.PDF],
    )
result: AnalyzeResult = poller.result()


# Print the extracted text to the console
if hasattr(result, "content"):
    print(result.content)
else:
    print("No text content found in the analysis result.")