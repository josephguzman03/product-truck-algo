from dotenv import load_dotenv
import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import json

load_dotenv()

client = DocumentIntelligenceClient(
    endpoint=os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
    credential=AzureKeyCredential(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY'))
)

with open('data/receipts/1.jpg', 'rb') as f:
    poller = client.begin_analyze_document(model_id='prebuilt-receipt', body=f)

result = poller.result()

if result.documents:
    doc = result.documents[0]
    print("=== ALL FIELDS ===")
    for field_name, field in doc.fields.items():
        print(f"\n{field_name}:")
        print(f"  Type: {type(field).__name__}")
        print(f"  Content: {field.content if hasattr(field, 'content') else 'N/A'}")
        
        # If it's Items, print structure
        if field_name == "Items":
            print(f"  Has value_array: {hasattr(field, 'value_array')}")
            
            # Try to get items using value_array
            try:
                items_array = field.value_array
                print(f"  Items found: {len(items_array) if items_array else 0}")
                
                if items_array:
                    for idx, item in enumerate(items_array):
                        print(f"\n  Item {idx}:")
                        print(f"    Type: {type(item).__name__}")
                        print(f"    Has value_object: {hasattr(item, 'value_object')}")
                        
                        if hasattr(item, 'value_object') and item.value_object:
                            print(f"    Properties:")
                            for key, val in item.value_object.items():
                                val_content = val.content if hasattr(val, 'content') else str(val)
                                print(f"      {key}: {val_content}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()