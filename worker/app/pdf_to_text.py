from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    with open(pdf_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-read",
            body=f,
            output=[AnalyzeOutputOption.PDF],
        )
    result: AnalyzeResult = poller.result()

    if hasattr(result, "content"):
        return result.content
    else:
        return ""

# Example usage:
# text = extract_text_from_pdf("resume.pdf")
# print(text)