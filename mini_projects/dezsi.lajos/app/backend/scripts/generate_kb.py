import os
from fpdf import FPDF

# Ensure directories exist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
os.makedirs(KB_DIR, exist_ok=True)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Medical Support Knowledge Base', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 10, body)
        self.ln()

def create_tier1_doc():
    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title("Tier 1 Support: Basic Troubleshooting & Routine Requests")
    
    intro = """
    Scope: Basic troubleshooting, "How-to" questions, Password/Login issues, Routine requests.
    Responsible Party: 3rd Party Service Provider, Client Local Admin, Vendor GSC.
    """
    pdf.chapter_body(intro)
    
    pdf.chapter_title("1. Password & Login Issues")
    body = """
    - Locked Account: Check if the user has tried 3+ times. Verify identity via SMS or email code before unlocking.
    - Forgot Password: Guide user to the 'Forgot Password' link on the login page.
    - SSO Errors: If Single Sign-On fails, ensure the user is on the corporate VPN. Clear browser cookies/cache.
    """
    pdf.chapter_body(body)
    
    pdf.chapter_title("2. Basic Troubleshooting")
    body = """
    - Application Slowness: Ask user to check internet connection (speedtest). Restart the browser.
    - Browser Compatibility: Ensure user is using Chrome or Edge (latest versions). Firefox is partially supported. IE is deprecated.
    - Printer Issues: Verify the printer is selected in the print dialog. If 'Print to PDF' works, it's a hardware/network issue.
    """
    pdf.chapter_body(body)
    
    pdf.chapter_title("3. Routine Access Requests")
    body = """
    - New User Setup: Requires approval from Department Head. Form ID: ACC-01.
    - Folder Access: Read-only access can be granted by Tier 1. Write access requires Tier 2 approval.
    """
    pdf.chapter_body(body)

    filename = os.path.join(KB_DIR, "Tier_1_Support.pdf")
    pdf.output(filename)
    print(f"Generated: {filename}")

def create_tier2_doc():
    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title("Tier 2 Support: Advanced Technical Support")
    
    intro = """
    Scope: Issues escalated by L1, Deeper investigation, Complex user management, Data issues, Diagnosing integration errors.
    Responsible Party: Advanced Support Team, System Admins.
    """
    pdf.chapter_body(intro)
    
    pdf.chapter_title("1. Integration Errors")
    body = """
    - API Timeouts: If external lab results are not syncing, check the 'Integration Logs' in the admin panel. 
      Error 504 usually means the HIE (Health Information Exchange) is down.
    - HL7 Mismatch: If patient data doesn't match, verify the MRN (Medical Record Number) formatting. 
      Leading zeros are often stripped by Excel imports.
    """
    pdf.chapter_body(body)
    
    pdf.chapter_title("2. Complex User Management")
    body = """
    - Role Based Access Control (RBAC): Modifying permission groups (e.g., granting 'Prescribe' rights) requires Medical Director sign-off.
    - Multi-Tenant Issues: If a user sees patients from another clinic, check the 'TenantID' binding in the user profile table immediately.
    """
    pdf.chapter_body(body)
    
    pdf.chapter_title("3. Data Consistency")
    body = """
    - Duplicate Patients: Use the 'Merge Patient' tool. Valid from 2024-01-01 policy update.
    - Missing Lab Reports: Check 'orphaned_results' table. Often caused by mismatched DOBs.
    """
    pdf.chapter_body(body)

    filename = os.path.join(KB_DIR, "Tier_2_Support.pdf")
    pdf.output(filename)
    print(f"Generated: {filename}")

if __name__ == "__main__":
    try:
        create_tier1_doc()
        create_tier2_doc()
    except ImportError:
        print("Error: fpdf module not found. Please run 'pip install fpdf'")
    except Exception as e:
        print(f"An error occurred: {e}")
