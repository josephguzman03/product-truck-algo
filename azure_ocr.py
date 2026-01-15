from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import json

class AzureReceiptParser:
    def __init__(self, api_key, endpoint):
        self.api_key = api_key
        self.endpoint = endpoint
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint, 
            credential=AzureKeyCredential(api_key)
        )
    
    def process_receipt(self, image_path):
        """
        Process a receipt image and extract structured data.
        Returns a dict with: merchant, date, items, subtotal, tax, total
        """
        with open(image_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-receipt",
                body=f
            )
        
        result = poller.result()
        
        # Extract key info
        receipt_data = {
            "merchant": None,
            "date": None,
            "items": [],
            "subtotal": None,
            "tax": None,
            "total": None
        }
        
        # Get document fields
        if result.documents:
            for field_name, field in result.documents[0].fields.items():
                if field_name == "MerchantName" and field.content:
                    receipt_data["merchant"] = field.content
                elif field_name == "TransactionDate" and field.content:
                    receipt_data["date"] = field.content
                elif field_name == "Subtotal" and field.content:
                    receipt_data["subtotal"] = field.content
                elif field_name == "TotalTax" and field.content:
                    receipt_data["tax"] = field.content
                elif field_name == "Total" and field.content:
                    receipt_data["total"] = field.content
                elif field_name == "Items":
                    # Use value_array to get the items
                    items_array = field.value_array
                    if items_array:
                        for item in items_array:
                            item_dict = {}
                            # item should be a DocumentField with properties
                            if hasattr(item, 'value_object') and item.value_object:
                                for key, val in item.value_object.items():
                                    if hasattr(val, 'content'):
                                        item_dict[key] = val.content
                                    else:
                                        item_dict[key] = str(val)
                            receipt_data["items"].append(item_dict)
        
        return receipt_data
    
    def process_receipts_batch(self, image_paths):
        """Process multiple receipts and return list of results"""
        results = []
        for path in image_paths:
            try:
                result = self.process_receipt(path)
                result["file"] = path
                results.append(result)
            except Exception as e:
                print(f"Error processing {path}: {str(e)}")
                results.append({"file": path, "error": str(e)})
        
        return results
    
    def save_to_json(self, receipt_data, output_path):
        """Save extracted data to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(receipt_data, f, indent=2, default=str)