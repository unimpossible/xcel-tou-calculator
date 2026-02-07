import pdfplumber
import sys
from collections import defaultdict

from datetime import datetime

def open_pdf(file_path):
    return pdfplumber.open(file_path)

def get_statement_date(tables):
    for table in tables:
        for i, row in enumerate(table):
            # Clean and normalize row for searching
            cleaned_row = [str(cell).replace(" ", "").replace("\n", "").upper() if cell else "" for cell in row]
            if "STATEMENTDATE" in cleaned_row:
                col_idx = cleaned_row.index("STATEMENTDATE")
                # Look for the value in subsequent rows
                for subsequent_row in table[i+1:]:
                    val = subsequent_row[col_idx]
                    if val and val.strip():
                        return val
    return None

def is_bill_winter(pdf):
    page_one = pdf.pages[0]
    tables = page_one.extract_tables()
    date_str = get_statement_date(tables)
    
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y")
            # Xcel Summer is typically June-September. Winter is Oct-May.
            if 6 <= dt.month <= 9:
                return False # Is Summer
            return True # Is Winter
        except ValueError:
            pass
    return None # Could not determine
    

def extract_usage_from_pdf(pdf):
    usage = defaultdict(list)
    for page in pdf.pages:
        tables = page.extract_tables()
        text = page.extract_text_simple()
        # skip gas
        if "electricityservice" not in text.lower():
            continue
        for table in tables:
            for row in table:
                heading = row[0]
                if heading and "energy" in heading.lower():
                    actual_value = 0
                    for cell in row:
                        if cell and "actual" in cell.lower():
                            try:
                                # specific logic to handle "32 Actual" -> 32.0
                                actual_value += int(cell.split()[0])
                            except (ValueError, IndexError):
                                raise Exception("Invalid data format")
                    usage[heading] = actual_value

    return usage

def plan_cost(usage: dict, rate_plan: dict) -> float:
    total_cost = 0
    # Note: rate_plan might not have MidPkEnergy, so we use Off-PeakEnergy as fallback if logic dictates,
    effective_rate_plan = rate_plan.copy()
    if 'MidPkEnergy' not in effective_rate_plan:
        effective_rate_plan["MidPkEnergy"] = effective_rate_plan.get("Off-PeakEnergy", 0)

    for usage_type, usage_value in usage.items():
        if usage_type in effective_rate_plan:
            total_cost += usage_value * effective_rate_plan[usage_type]
            
    return total_cost
        

if __name__ == "__main__":
    pdf = open_pdf(sys.argv[1])
    tables = pdf.pages[0].extract_tables()
    print(f"Date: {get_statement_date(tables)}")
    print(f"Is Winter: {is_bill_winter(pdf)}")
    
    usage = extract_usage_from_pdf(pdf)
    print(usage)