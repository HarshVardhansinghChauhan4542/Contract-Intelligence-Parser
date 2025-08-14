import PyPDF2
import re
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from .database import get_database
from .models import ExtractedData, Gap
from .config import settings

class ContractProcessor:
    def __init__(self):
        self.huggingface_api_url = "https://api-inference.huggingface.co/models/"
        self.huggingface_headers = {}
        if settings.huggingface_api_key:
            self.huggingface_headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
    
    async def process_contract(self, contract_id: str, file_path: str):
        """Process contract and extract data"""
        db = await get_database()
        
        try:
            print(f"Starting processing for contract {contract_id}")
            
            # Update status to processing
            await db.contracts.update_one(
                {"contract_id": contract_id},
                {"$set": {"status": "processing", "progress": 10}}
            )
            
            # Extract text from PDF
            print(f"Extracting text from PDF: {file_path}")
            text = await self.extract_text_from_pdf(file_path)
            print(f"Extracted {len(text)} characters from PDF")
            
            await db.contracts.update_one(
                {"contract_id": contract_id},
                {"$set": {"progress": 30}}
            )
            
            # Extract structured data
            print(f"Extracting structured data...")
            extracted_data = await self.extract_contract_data(text)
            print(f"Extracted data - Parties: {len(extracted_data.parties)}, Financial: {extracted_data.financial_details is not None}")
            
            await db.contracts.update_one(
                {"contract_id": contract_id},
                {"$set": {"progress": 70}}
            )
            
            # Calculate score and identify gaps
            print(f"Calculating score and gaps...")
            score, gaps = await self.calculate_score_and_gaps(extracted_data)
            print(f"Calculated score: {score}, Gaps: {len(gaps)}")
            
            await db.contracts.update_one(
                {"contract_id": contract_id},
                {"$set": {"progress": 90}}
            )
            
            # Convert to dict for storage
            extracted_data_dict = extracted_data.dict() if hasattr(extracted_data, 'dict') else {}
            gaps_dict = [gap.dict() if hasattr(gap, 'dict') else gap for gap in gaps]
            
            # Update final results
            print(f"Saving final results...")
            await db.contracts.update_one(
                {"contract_id": contract_id},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100,
                        "extracted_data": extracted_data_dict,
                        "score": score,
                        "gaps": gaps_dict,
                        "processed_at": datetime.utcnow()
                    }
                }
            )
            
            print(f"Successfully processed contract {contract_id}")
            
        except Exception as e:
            print(f"Error processing contract {contract_id}: {e}")
            import traceback
            traceback.print_exc()
            
            # Update error status
            await db.contracts.update_one(
                {"contract_id": contract_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "processed_at": datetime.utcnow()
                    }
                }
            )
    
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file with robust error handling"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is readable
                if len(pdf_reader.pages) == 0:
                    raise ValueError("PDF has no pages")
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += page_text + "\n"
                        else:
                            print(f"Warning: No text extracted from page {page_num + 1}")
                    except Exception as e:
                        print(f"Error extracting text from page {page_num + 1}: {e}")
                        continue
                
                # If no text was extracted, try alternative method
                if not text.strip():
                    print("No text extracted with standard method, trying alternative extraction...")
                    text = await self._extract_text_alternative(file_path)
                
                # Clean up the extracted text
                text = self._clean_extracted_text(text)
                
                if not text.strip():
                    raise ValueError("No readable text content found in PDF")
                
                return text
                
        except Exception as e:
            print(f"Error extracting text from PDF {file_path}: {e}")
            raise ValueError(f"Failed to extract text from PDF: {e}")
    
    async def _extract_text_alternative(self, file_path: str) -> str:
        """Alternative PDF text extraction method for problematic PDFs"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    try:
                        # Try different extraction methods
                        if hasattr(page, 'extract_text'):
                            page_text = page.extract_text()
                        else:
                            page_text = ""
                        
                        if page_text:
                            text += page_text + "\n"
                    except:
                        continue
                return text
        except Exception as e:
            print(f"Alternative extraction failed: {e}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    async def extract_contract_data(self, text: str) -> ExtractedData:
        """Extract structured data from contract text"""
        try:
            # Use regex patterns and AI for extraction
            extracted_data = ExtractedData()
            
            # Extract parties - convert to proper model format
            parties_data = self.extract_parties(text)
            if parties_data:
                from .models import PartyInfo
                extracted_data.parties = [PartyInfo(**party) for party in parties_data]
            
            # Extract financial details - convert to proper model format
            financial_data = self.extract_financial_details(text)
            if financial_data:
                from .models import FinancialDetails, LineItem
                # Convert line items
                line_items = []
                for item_data in financial_data.get("line_items", []):
                    if isinstance(item_data, dict):
                        line_items.append(LineItem(**item_data))
                financial_data["line_items"] = line_items
                extracted_data.financial_details = FinancialDetails(**financial_data)
            
            # Extract payment structure - convert to proper model format
            payment_data = self.extract_payment_structure(text)
            if payment_data:
                from .models import PaymentStructure
                extracted_data.payment_structure = PaymentStructure(**payment_data)
            
            # Extract revenue classification - convert to proper model format
            revenue_data = self.extract_revenue_classification(text)
            if revenue_data:
                from .models import RevenueClassification
                extracted_data.revenue_classification = RevenueClassification(**revenue_data)
            
            # Extract SLA information - convert to proper model format
            sla_data = self.extract_sla(text)
            if sla_data:
                from .models import ServiceLevelAgreement
                extracted_data.sla = ServiceLevelAgreement(**sla_data)
            
            # Extract account information - convert to proper model format
            account_data = self.extract_account_info(text)
            if account_data:
                from .models import AccountInfo
                extracted_data.account_info = AccountInfo(**account_data)
            
            # Calculate confidence scores
            extracted_data.confidence_scores = self.calculate_confidence_scores(extracted_data, text)
            
            # Use AI for better extraction if Hugging Face key is available
            if settings.huggingface_api_key:
                extracted_data = await self.enhance_with_ai(extracted_data, text)
            
            return extracted_data
        
        except Exception as e:
            print(f"Error in extract_contract_data: {e}")
            # Return minimal data structure to prevent complete failure
            return ExtractedData()
    
    def extract_parties(self, text: str) -> List:
        """Extract party information using comprehensive regex patterns"""
        parties = []
        found_names = set()  # Track found names to avoid duplicates
        
        # Enhanced company name patterns (more selective)
        company_patterns = [
            # PARTY A/B specific patterns
            r'PARTY\s+[AB]:\s*([A-Za-z][a-zA-Z\s&.,\-\']*?(?:Inc\.|LLC|Corp\.|Corporation|Company|Ltd\.|Limited))',
            
            # Any line that ends with corporate suffix
            r'\b([A-Za-z][a-zA-Z\s&.,\-\']{3,40}?(?:Inc\.|LLC|Corp\.|Corporation|Company|Ltd\.|Limited))\b',
        ]
        
        # Extract parties using all patterns
        for pattern in company_patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                # Handle tuple results from multiple groups
                if matches and isinstance(matches[0], tuple):
                    # Flatten tuples from 'between X and Y' pattern
                    flat_matches = []
                    for match_tuple in matches:
                        for match in match_tuple:
                            if match.strip():
                                flat_matches.append(match)
                    matches = flat_matches
                
                for match in matches:
                    name = match.strip()
                    
                    # Clean up the name
                    name = re.sub(r',$', '', name)  # Remove trailing comma only
                    name = re.sub(r'\s+', ' ', name)   # Normalize whitespace
                    
                    # Validate the name - more strict validation
                    if (len(name) > 3 and 
                        len(name) < 80 and 
                        name not in found_names and
                        not re.match(r'^\d+$', name) and  # Not just numbers
                        not name.lower() in ['the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'legal entity', 'entity', 'delaware corporation', 'limited liability company'] and
                        # Must contain actual company identifiers
                        re.search(r'\b(?:Inc\.?|LLC|Corp\.?|Corporation|Company|Ltd\.?|Limited)\b', name, re.IGNORECASE) and
                        # Must have a proper company name (not just entity type)
                        not re.match(r'^(?:Delaware|California|New York|Nevada)\s+Corporation$', name, re.IGNORECASE) and
                        not re.match(r'^Limited Liability Company$', name, re.IGNORECASE)):
                        
                        found_names.add(name)
                        
                        # Determine entity type
                        entity_type = None
                        if re.search(r'\b(?:Inc\.?|Corporation|Corp\.?)\b', name, re.IGNORECASE):
                            entity_type = "Corporation"
                        elif re.search(r'\bLLC\b', name, re.IGNORECASE):
                            entity_type = "Limited Liability Company"
                        elif re.search(r'\b(?:Ltd\.?|Limited)\b', name, re.IGNORECASE):
                            entity_type = "Limited Company"
                        
                        parties.append({
                            "name": name,
                            "legal_entity": entity_type,
                            "registration_details": None,
                            "signatories": [],
                            "roles": []
                        })
            except Exception as e:
                print(f"Error in pattern {pattern}: {e}")
                continue
        
        # Look for signatories if we have parties
        if parties:
            signatory_patterns = [
                r'(?:Signed|Signature|By):\s*([A-Z][a-zA-Z\s\.]{3,30})',
                r'([A-Z][a-zA-Z\s\.]{3,30}),?\s+(?:CEO|CFO|President|Vice President|Director|Manager)',
                r'(?:CEO|CFO|President|Vice President|Director|Manager):\s*([A-Z][a-zA-Z\s\.]{3,30})'
            ]
            
            for pattern in signatory_patterns:
                try:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        signatory = match.strip()
                        if len(signatory) > 3 and len(signatory) < 50:
                            # Add to first party (can be improved with better matching)
                            if parties and len(parties[0]["signatories"]) < 3:
                                parties[0]["signatories"].append(signatory)
                except Exception as e:
                    continue
        
        # Remove duplicates while preserving order
        unique_parties = []
        seen_names = set()
        for party in parties:
            if party["name"] not in seen_names:
                seen_names.add(party["name"])
                unique_parties.append(party)
        
        return unique_parties[:10]  # Limit to 10 parties
    
    def extract_financial_details(self, text: str) -> Dict:
        """Extract comprehensive financial information"""
        financial_details = {
            "line_items": [],
            "total_value": None,
            "currency": None,
            "tax_info": None,
            "additional_fees": []
        }
        
        
        currency_patterns = [
            (r'\$', 'USD'),
            (r'USD|US\$|US Dollar', 'USD'),
            (r'CAD|CA\$|Canadian Dollar', 'CAD'),
            (r'EUR|€|Euro', 'EUR'),
            (r'GBP|£|British Pound', 'GBP'),
            (r'AUD|AU\$|Australian Dollar', 'AUD'),
            (r'JPY|¥|Japanese Yen', 'JPY')
        ]
        
        for pattern, currency_code in currency_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                financial_details["currency"] = currency_code
                break
        
        
        money_patterns = [
            
            r'(?:USD|CAD|EUR|GBP|AUD)\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)',
            r'€\s*([\d,]+\.?\d*)',
            r'£\s*([\d,]+\.?\d*)',
            
            
            r'(?:total|amount|sum|fee|cost|price|value|payment)\s*[:\s]*(?:USD|CAD|EUR|GBP|AUD)?\s*\$?\s*([\d,]+\.?\d*)',
            r'(?:monthly|annual|yearly)\s*(?:fee|cost|payment)\s*[:\s]*\$?\s*([\d,]+\.?\d*)',
            
            
            r'(?:contract|agreement)\s*(?:value|amount|total)\s*[:\s]*\$?\s*([\d,]+\.?\d*)',
            
            
            r'\$\s*([\d,]+\.?\d*)\s*(?:USD|CAD|EUR|GBP)?',
        ]
        
        amounts = []
        amount_contexts = []
        
        for pattern in money_patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    amount_str = match.group(1)
                    try:
                        amount = float(amount_str.replace(',', ''))
                        if 0 < amount < 1000000000:  
                            amounts.append(amount)
                            

                            start = max(0, match.start() - 50)
                            end = min(len(text), match.end() + 50)
                            context = text[start:end].strip()
                            amount_contexts.append((amount, context))
                    except ValueError:
                        continue
            except Exception as e:
                print(f"Error in money pattern {pattern}: {e}")
                continue
        
        
        if amounts:
            
            total_indicators = [
                'total', 'sum', 'amount', 'contract value', 'total value', 
                'grand total', 'final amount', 'total cost', 'total price'
            ]
            
            total_value = None
            
            
            for amount, context in amount_contexts:
                context_lower = context.lower()
                if any(indicator in context_lower for indicator in total_indicators):
                    if not total_value or amount > total_value:
                        total_value = amount
            
            
            if not total_value:
                total_value = max(amounts)
            
            financial_details["total_value"] = total_value
        

        line_item_patterns = [
            r'(?:^|\n)\s*[-•*]\s*([^:]+?):\s*\$?\s*([\d,]+\.?\d*)',
            r'(?:^|\n)\s*(\d+\.?\d*)\.\s*([^:]+?)\s*[-:]\s*\$?\s*([\d,]+\.?\d*)',
            r'([A-Za-z][^:]{5,30})\s*[-:]\s*(?:Quantity|Qty):\s*(\d+)\s*[-:]\s*(?:Unit Price|Price):\s*\$?\s*([\d,]+\.?\d*)\s*[-:]\s*(?:Total):\s*\$?\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in line_item_patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    try:
                        if len(match) == 2:  
                            description, amount_str = match
                            amount = float(amount_str.replace(',', ''))
                            financial_details["line_items"].append({
                                "description": description.strip(),
                                "quantity": None,
                                "unit_price": None,
                                "total": amount
                            })
                        elif len(match) == 4:  
                            description, qty_str, price_str, total_str = match
                            quantity = float(qty_str.replace(',', ''))
                            unit_price = float(price_str.replace(',', ''))
                            total = float(total_str.replace(',', ''))
                            financial_details["line_items"].append({
                                "description": description.strip(),
                                "quantity": quantity,
                                "unit_price": unit_price,
                                "total": total
                            })
                    except (ValueError, IndexError):
                        continue
            except Exception as e:
                print(f"Error extracting line items: {e}")
                continue
        

        tax_patterns = [
            r'(?:tax|VAT|GST|HST)\s*[:\s]*(\d+\.?\d*)\s*%',
            r'(?:tax|VAT|GST|HST)\s*[:\s]*\$?\s*([\d,]+\.?\d*)',
            r'(?:plus|including|excluding)\s*(?:tax|VAT|GST|HST)'
        ]
        
        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                financial_details["tax_info"] = match.group(0)
                break
        
        return financial_details
    
    def extract_payment_structure(self, text: str) -> Dict:
        """Extract payment terms and structure with improved accuracy"""
        payment_structure = {
            "payment_terms": None,
            "payment_schedules": [],
            "due_dates": [],
            "payment_methods": [],
            "banking_details": None
        }
        
        
        terms_patterns = [
            r'(?:Payment Terms?|Terms?):\s*(Net\s+\d+(?:\s+days?)?)',
            r'(Net\s+\d+(?:\s+days?)?)',
            r'payment[\s\w]*due[\s\w]*(\d+\s+days?)',
            r'(\d+\s+days?\s*from\s*invoice)',
            r'due\s*(?:in|within)?\s*(\d+\s*days?)',
            r'payment\s*within\s*(\d+\s*days?)',
        ]
        
        for pattern in terms_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                term = match.group(1).strip()
                
                term = re.sub(r'\s+', ' ', term)
                if 'Net' not in term and 'day' in term.lower():
                    term = f"Net {term}"
                payment_structure["payment_terms"] = term
                break
        
        
        method_patterns = [
            r'(?:Payment Methods?|Methods?|Pay by):\s*([^.]+)',
            r'(?:via|through|by)\s*(credit card|wire transfer|ACH|check|bank transfer|electronic payment|direct deposit|paypal)',
            r'(credit card|wire transfer|ACH|check|bank transfer|electronic payment|direct deposit|paypal)',
        ]
        
        found_methods = set()  
        
        for pattern in method_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    method = match[0] if match[0] else match[-1]
                else:
                    method = match
                
                
                method = method.strip().lower()
                
                
                methods_list = re.split(r'[,;/&]|\sand\s|\sor\s', method)
                for m in methods_list:
                    m = m.strip()
                    if len(m) > 2 and m not in ['or', 'and', 'via', 'by', 'through']:
                        
                        if 'credit' in m and 'card' in m:
                            found_methods.add("Credit Card")
                        elif 'wire' in m and 'transfer' in m:
                            found_methods.add("Wire Transfer")
                        elif 'ach' in m:
                            found_methods.add("ACH")
                        elif 'check' in m:
                            found_methods.add("Check")
                        elif 'bank' in m and 'transfer' in m:
                            found_methods.add("Bank Transfer")
                        elif 'electronic' in m and 'payment' in m:
                            found_methods.add("Electronic Payment")
                        elif 'direct' in m and 'deposit' in m:
                            found_methods.add("Direct Deposit")
                        elif 'paypal' in m:
                            found_methods.add("PayPal")
                        else:
                            # Capitalize first letter of each word
                            found_methods.add(m.title())
        
        payment_structure["payment_methods"] = list(found_methods)
        
        # Extract payment schedules
        schedule_patterns = [
            r'(monthly|quarterly|annually|yearly|weekly|bi-weekly)\s*(?:payment|billing|invoicing)',
            r'(?:payment|billing|invoicing)\s*(monthly|quarterly|annually|yearly|weekly|bi-weekly)',
            r'(monthly|quarterly|annually|yearly|weekly|bi-weekly)\s*basis',
        ]
        
        for pattern in schedule_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                schedule = match.strip().capitalize()
                if schedule not in payment_structure["payment_schedules"]:
                    payment_structure["payment_schedules"].append(schedule)
        
        # Extract due dates
        date_patterns = [
            r'due\s*(?:on|by)?\s*(\d{1,2}(?:st|nd|rd|th)?\s*of\s*each\s*month)',
            r'payment\s*due\s*(\w+\s*\d{1,2},?\s*\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                date = match.strip()
                if date not in payment_structure["due_dates"]:
                    payment_structure["due_dates"].append(date)
        
        # Extract banking details
        banking_patterns = [
            r'(?:Account|Acct)\s*(?:Number|#):\s*([A-Z0-9\-]+)',
            r'(?:Routing|ABA)\s*(?:Number|#):\s*([0-9\-]+)',
            r'Banking Details?:\s*([^.]+)',
        ]
        
        for pattern in banking_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                payment_structure["banking_details"] = match.group(1).strip()
                break
        
        return payment_structure
    
    def extract_revenue_classification(self, text: str) -> Dict:
        """Extract revenue classification information"""
        revenue_classification = {
            "recurring_payments": False,
            "one_time_payments": False,
            "subscription_model": None,
            "billing_cycle": None,
            "renewal_terms": None,
            "auto_renewal": False
        }
        
        
        recurring_patterns = [
            r'recurring|subscription|monthly|quarterly|annually|yearly',
            r'auto.?renew|automatic.?renewal'
        ]
        
        for pattern in recurring_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                revenue_classification["recurring_payments"] = True
                break
        
        
        onetime_patterns = [r'one.?time|single payment|lump sum']
        for pattern in onetime_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                revenue_classification["one_time_payments"] = True
                break
        
        
        cycle_patterns = [r'(monthly|quarterly|annually|yearly|weekly)']
        cycle_match = re.search('|'.join(cycle_patterns), text, re.IGNORECASE)
        if cycle_match:
            revenue_classification["billing_cycle"] = cycle_match.group(1)
        
        return revenue_classification
    
    def extract_sla(self, text: str) -> Dict:
        """Extract Service Level Agreement information"""
        sla = {
            "performance_metrics": [],
            "benchmarks": [],
            "penalty_clauses": [],
            "remedies": [],
            "support_terms": None,
            "maintenance_terms": None
        }
        
        # Extract performance metrics
        metric_patterns = [
            r'(\d+\.?\d*%\s*(?:uptime|availability|performance))',
            r'((?:uptime|availability):\s*\d+\.?\d*%)',
            r'(response time[:\s]+(?:maximum\s+)?\d+\s+(?:seconds?|minutes?|hours?))',
            r'(support response[:\s]+\d+\s+(?:hours?|minutes?))',
            r'(\d+\s+(?:seconds?|minutes?|hours?)\s+(?:response|support))',
        ]
        
        for pattern in metric_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                metric = match.strip()
                if metric and metric not in sla["performance_metrics"]:
                    sla["performance_metrics"].append(metric)
        
        return sla
    
    def extract_account_info(self, text: str) -> Dict:
        """Extract account information"""
        account_info = {
            "billing_details": None,
            "account_numbers": [],
            "contact_info": {}
        }
        
        # Extract account numbers
        account_patterns = [
            r'account[\s#]*:?\s*([A-Z0-9\-]+)',
            r'customer[\s#]*:?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in account_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            account_info["account_numbers"].extend(matches)
        
        # Extract contact information
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        phone_patterns = [
            r'\((\d{3})\)\s*(\d{3})-?(\d{4})',  
            r'(\d{3})[-.](\d{3})[-.](\d{4})',   
            r'(\d{3})\s+(\d{3})\s+(\d{4})',    
        ]
        
        emails = re.findall(email_pattern, text)
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    
                    phone = f"({match[0]}) {match[1]}-{match[2]}"
                else:
                    phone = match
                phones.append(phone)
        
        if emails:
            account_info["contact_info"]["emails"] = emails
        if phones:
            account_info["contact_info"]["phones"] = phones
        
        return account_info
    
    def calculate_confidence_scores(self, extracted_data: ExtractedData, text: str) -> Dict[str, float]:
        """Calculate confidence scores for extracted data"""
        scores = {}
        
        
        financial_score = 0.0
        if extracted_data.financial_details:
            if hasattr(extracted_data.financial_details, 'total_value') and extracted_data.financial_details.total_value:
                financial_score += 0.4
            if hasattr(extracted_data.financial_details, 'currency') and extracted_data.financial_details.currency:
                financial_score += 0.3
            if hasattr(extracted_data.financial_details, 'line_items') and extracted_data.financial_details.line_items:
                financial_score += 0.3
        scores["financial"] = financial_score
        
        
        party_score = 0.0
        if extracted_data.parties:
            party_score = 0.5
            if len(extracted_data.parties) >= 2:
                party_score = 0.8
            
            for party in extracted_data.parties:
                if hasattr(party, 'signatories') and party.signatories:
                    party_score = min(1.0, party_score + 0.1)
                if hasattr(party, 'legal_entity') and party.legal_entity:
                    party_score = min(1.0, party_score + 0.1)
        scores["parties"] = party_score
        
        
        payment_score = 0.0
        if extracted_data.payment_structure:
            if hasattr(extracted_data.payment_structure, 'payment_terms') and extracted_data.payment_structure.payment_terms:
                payment_score += 0.6
            if hasattr(extracted_data.payment_structure, 'payment_methods') and extracted_data.payment_structure.payment_methods:
                payment_score += 0.4
        scores["payment"] = payment_score
        
        
        sla_score = 0.0
        if extracted_data.sla:
            if hasattr(extracted_data.sla, 'performance_metrics') and extracted_data.sla.performance_metrics:
                sla_score += 0.5
            if hasattr(extracted_data.sla, 'support_terms') and extracted_data.sla.support_terms:
                sla_score += 0.5
        scores["sla"] = sla_score
        
        
        contact_score = 0.0
        if extracted_data.account_info:
            if hasattr(extracted_data.account_info, 'contact_info') and extracted_data.account_info.contact_info:
                contact_info = extracted_data.account_info.contact_info
                if isinstance(contact_info, dict):
                    if contact_info.get("emails"):
                        contact_score += 0.5
                    if contact_info.get("phones"):
                        contact_score += 0.5
        scores["contact"] = contact_score
        
        return scores
    
    async def enhance_with_ai(self, extracted_data: ExtractedData, text: str) -> ExtractedData:
        try:
            
            model_url = f"{self.huggingface_api_url}facebook/bart-large-mnli"
            
            
            queries = [
                "This text contains company names and parties",
                "This text contains financial amounts and currency",
                "This text contains payment terms and methods",
                "This text contains service level agreements",
                "This text contains contact information"
            ]
            
            enhanced_confidence = {}
            
            for query in queries:
                payload = {
                    "inputs": {
                        "text": text[:1000],  
                        "candidate_labels": [query]
                    }
                }
                
                try:
                    response = requests.post(
                        model_url,
                        headers=self.huggingface_headers,
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'scores' in result and len(result['scores']) > 0:
                            confidence = result['scores'][0]
                            query_key = query.split()[-1].lower()  
                            enhanced_confidence[query_key] = confidence
                
                except Exception as e:
                    continue
            
            
            if enhanced_confidence:
                for key, value in enhanced_confidence.items():
                    if key in extracted_data.confidence_scores:
                        
                        extracted_data.confidence_scores[key] = (
                            extracted_data.confidence_scores[key] + value
                        ) / 2
            

            await self._extract_with_text_generation(extracted_data, text)
            
        except Exception as e:
            print(f"AI enhancement failed: {e}")
        
        return extracted_data
    
    async def _extract_with_text_generation(self, extracted_data: ExtractedData, text: str):
        """Use text generation model to extract structured data"""
        try:
            model_url = f"{self.huggingface_api_url}microsoft/DialoGPT-medium"
            
            prompt = f"""
            Analyze this contract and extract:
            - Company names
            - Financial amounts
            - Payment terms
            
            Contract: {text[:500]}
            
            Extract:"""
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.1,
                    "do_sample": False
                }
            }
            
            response = requests.post(
                model_url,
                headers=self.huggingface_headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    self._parse_ai_response(extracted_data, generated_text)
        
        except Exception as e:
            print(f"Text generation failed: {e}")
    
    def _parse_ai_response(self, extracted_data: ExtractedData, ai_text: str):
        """Parse AI-generated text and enhance extracted data"""
        try:
            company_pattern = r'(?:Company|Corp|Inc|LLC|Ltd)[\w\s]+'
            ai_companies = re.findall(company_pattern, ai_text, re.IGNORECASE)
            
            existing_parties = [party.name for party in extracted_data.parties]
            for company in ai_companies:
                company = company.strip()
                if company and len(company) > 3 and company not in existing_parties:
                    from .models import PartyInfo
                    extracted_data.parties.append(PartyInfo(
                        name=company,
                        legal_entity=None,
                        registration_details=None,
                        signatories=[],
                        roles=[]
                    ))
            
            amount_pattern = r'\$[\d,]+\.?\d*'
            ai_amounts = re.findall(amount_pattern, ai_text)
            
            if ai_amounts and extracted_data.financial_details:
                for amount_str in ai_amounts:
                    try:
                        amount = float(amount_str.replace('$', '').replace(',', ''))
                        if not extracted_data.financial_details.total_value or amount > extracted_data.financial_details.total_value:
                            extracted_data.financial_details.total_value = amount
                    except ValueError:
                        continue
        
        except Exception as e:
            print(f"AI response parsing failed: {e}")
    
    async def calculate_score_and_gaps(self, extracted_data: ExtractedData) -> tuple[float, List[Gap]]:
        """Calculate overall score and identify gaps"""
        gaps = []
        
        financial_score = 0
        party_score = 0
        payment_score = 0
        sla_score = 0
        contact_score = 0
        
        if extracted_data.financial_details:
            if hasattr(extracted_data.financial_details, 'total_value') and extracted_data.financial_details.total_value:
                financial_score += 15
            else:
                gaps.append(Gap(
                    field="total_value",
                    description="Missing total contract value",
                    criticality="high"
                ))
            
            if hasattr(extracted_data.financial_details, 'currency') and extracted_data.financial_details.currency:
                financial_score += 10
            else:
                gaps.append(Gap(
                    field="currency",
                    description="Currency not specified",
                    criticality="medium"
                ))
            
            if hasattr(extracted_data.financial_details, 'line_items') and extracted_data.financial_details.line_items:
                financial_score += 5
        else:
            gaps.append(Gap(
                field="financial_details",
                description="Missing financial information including total value and currency",
                criticality="high"
            ))
        
        if extracted_data.parties and len(extracted_data.parties) >= 2:
            party_score = 25
        elif extracted_data.parties and len(extracted_data.parties) == 1:
            party_score = 15
            gaps.append(Gap(
                field="parties",
                description="Only one party identified, expected at least two parties",
                criticality="medium"
            ))
        else:
            gaps.append(Gap(
                field="parties",
                description="No contract parties identified",
                criticality="high"
            ))
        
        if extracted_data.payment_structure:
            if hasattr(extracted_data.payment_structure, 'payment_terms') and extracted_data.payment_structure.payment_terms:
                payment_score += 12
            else:
                gaps.append(Gap(
                    field="payment_terms",
                    description="Missing payment terms (e.g., Net 30)",
                    criticality="high"
                ))
            
            if hasattr(extracted_data.payment_structure, 'payment_methods') and extracted_data.payment_structure.payment_methods:
                payment_score += 8
            else:
                gaps.append(Gap(
                    field="payment_methods",
                    description="Payment methods not specified",
                    criticality="medium"
                ))
        else:
            gaps.append(Gap(
                field="payment_structure",
                description="Missing payment terms and methods",
                criticality="high"
            ))
        
        if extracted_data.sla:
            if hasattr(extracted_data.sla, 'performance_metrics') and extracted_data.sla.performance_metrics:
                sla_score += 10
            else:
                gaps.append(Gap(
                    field="performance_metrics",
                    description="Missing SLA performance metrics (uptime, response time)",
                    criticality="medium"
                ))
            
            if hasattr(extracted_data.sla, 'support_terms') and extracted_data.sla.support_terms:
                sla_score += 5
            else:
                gaps.append(Gap(
                    field="support_terms",
                    description="Support terms not defined",
                    criticality="low"
                ))
        else:
            gaps.append(Gap(
                field="sla",
                description="No service level agreements found",
                criticality="medium"
            ))
        
        if extracted_data.account_info and hasattr(extracted_data.account_info, 'contact_info') and extracted_data.account_info.contact_info:
            contact_info = extracted_data.account_info.contact_info
            if isinstance(contact_info, dict):
                if contact_info.get("emails"):
                    contact_score += 5
                else:
                    gaps.append(Gap(
                        field="contact_emails",
                        description="Missing contact email addresses",
                        criticality="low"
                    ))
                
                if contact_info.get("phones"):
                    contact_score += 5
                else:
                    gaps.append(Gap(
                        field="contact_phones",
                        description="Missing contact phone numbers",
                        criticality="low"
                    ))
            else:
                gaps.append(Gap(
                    field="contact_info",
                    description="Contact information format error",
                    criticality="low"
                ))
        else:
            gaps.append(Gap(
                field="contact_info",
                description="Missing contact information",
                criticality="low"
            ))
        
        total_score = financial_score + party_score + payment_score + sla_score + contact_score
        
        return total_score, gaps

