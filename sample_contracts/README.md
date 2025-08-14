# Sample Contracts for Testing

This directory contains sample contract documents to test the Contract Intelligence System with various contract types and formats.

## Test Cases Covered

### 1. Complete Service Agreement
- **File**: `service_agreement_complete.txt`
- **Description**: Well-structured service agreement with all required fields
- **Expected Score**: 90-100 points
- **Key Features**:
  - Clear party identification
  - Detailed financial terms
  - Comprehensive payment structure
  - Defined SLAs
  - Complete contact information

### 2. Minimal Contract
- **File**: `minimal_contract.txt`
- **Description**: Basic contract with limited information
- **Expected Score**: 30-50 points
- **Key Features**:
  - Basic party information
  - Minimal financial details
  - Missing SLAs and detailed terms

### 3. Software License Agreement
- **File**: `software_license.txt`
- **Description**: Software licensing contract with recurring payments
- **Expected Score**: 70-85 points
- **Key Features**:
  - Subscription-based revenue model
  - Auto-renewal clauses
  - Performance metrics
  - Multi-tier pricing

### 4. Consulting Agreement
- **File**: `consulting_agreement.txt`
- **Description**: Professional services contract with hourly billing
- **Expected Score**: 75-90 points
- **Key Features**:
  - Hourly rate structure
  - Project milestones
  - Intellectual property terms
  - Termination clauses

### 5. Missing Information Contract
- **File**: `incomplete_contract.txt`
- **Description**: Contract with deliberately missing critical fields
- **Expected Score**: 20-40 points
- **Gap Analysis**: High-priority gaps for missing fields

## Testing Instructions

1. **Upload via Web Interface**:
   - Navigate to http://localhost:3000
   - Use drag-and-drop to upload sample contracts
   - Monitor processing status
   - Review extracted data and scores

2. **API Testing**:
   ```bash
   # Upload contract via API
   curl -X POST "http://localhost:8000/contracts/upload" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@sample_contracts/service_agreement_complete.pdf"

   # Check processing status
   curl "http://localhost:8000/contracts/{contract_id}/status"

   # Get extracted data
   curl "http://localhost:8000/contracts/{contract_id}"
   ```

3. **Expected Results**:
   - Verify correct party extraction
   - Check financial data accuracy
   - Validate scoring algorithm
   - Review gap analysis results

## Creating Test PDFs

To convert text files to PDF for testing:

```bash
# Using pandoc (if available)
pandoc service_agreement_complete.txt -o service_agreement_complete.pdf

# Using Python (create_test_pdfs.py script)
python create_test_pdfs.py
```

## Edge Cases to Test

### File Upload Edge Cases
1. **Large Files**: Test with files approaching 50MB limit
2. **Invalid Formats**: Try uploading non-PDF files
3. **Corrupted PDFs**: Test with malformed PDF files
4. **Empty PDFs**: Upload PDFs with no text content

### Contract Content Edge Cases
1. **No Parties**: Contracts without clear party identification
2. **Multiple Currencies**: Contracts with different currency formats
3. **Complex Payment Terms**: Non-standard payment structures
4. **Foreign Language**: Non-English contract content
5. **Scanned Documents**: Image-based PDFs requiring OCR

### API Edge Cases
1. **Concurrent Uploads**: Multiple simultaneous file uploads
2. **Invalid Contract IDs**: Requests with non-existent contract IDs
3. **Processing Interruption**: System restart during processing
4. **Database Connectivity**: MongoDB connection failures

## Performance Testing

### Load Testing
Test system performance with:
- 10 concurrent users uploading contracts
- 100 contracts processed simultaneously
- Large contract files (40-50MB)
- Extended processing times

### Memory Testing
Monitor resource usage during:
- PDF text extraction
- AI-enhanced processing
- Database operations
- File storage operations

## Validation Checklist

After testing with sample contracts, verify:

- [ ] All expected fields are extracted correctly
- [ ] Scoring algorithm produces reasonable scores
- [ ] Gap analysis identifies missing information
- [ ] Confidence scores reflect extraction quality
- [ ] Processing status updates correctly
- [ ] Error handling works for invalid inputs
- [ ] UI displays data clearly
- [ ] Download functionality works
- [ ] Search and filtering operate correctly
- [ ] System performance is acceptable

## Adding New Test Cases

To add new test contract scenarios:

1. Create contract text file with specific test case
2. Convert to PDF format
3. Document expected extraction results
4. Add to test suite with validation criteria
5. Update this README with test case description
