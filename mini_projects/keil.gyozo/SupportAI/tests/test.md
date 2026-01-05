keilgyozo@PD-NB001 MINGW64 /c/Projects/SupportAI

$ curl -X POST http://localhost:8000/api/v1/tickets/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-TEST-001",
    "raw_message": "I was charged twice for my subscription this month",
    "customer_name": "John Doe",
    "customer_email": "john@example.com"
  }'

{"success":true,"ticket_id":"TKT-TEST-001","result":{"ticket_id":"TKT-TEST-001","timestamp":"2025-12-31T09:54:13.106348+00:00","triage":{"category":"Billing","subcategory":"Payments","priority":"P2","sla_hours":24,"suggested_team":"Finance Team","sentiment":"frustrated","confidence":0.9},"answer_draft":{"greeting":"Dear John Doe,","body":"I'm sorry to hear about the double charge on your subscription this month. I understand how frustrating this can be and I appreciate your patience as we resolve this issue. Unfortunately, our knowledge base does not have specific documentation on this issue. However, I assure you that we take billing issues very seriously. I will escalate this to our billing specialist who can provide detailed assistance and rectify the situation. You should expect to hear from them within the next 24-48 hours.","closing":"Thank you for bringing this to our attention. We value your business and are committed to resolving this issue promptly. If you have any other concerns, please don't hesitate to reach out.","tone":"empathetic_apologetic"},"citations":[],"policy_check":{"refund_promise":false,"sla_mentioned":true,"escalation_needed":true,"compliance":"warning","issues":["Specific SLA/timeline is mentioned without authorization","Issue requires escalation to specialist"]}}}


keilgyozo@PD-NB001 MINGW64 /c/Projects/SupportAI

$ curl -X POST http://localhost:8000/api/v1/tickets/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-TEST-002",
    "raw_message": "I bought a new phone and now I dont use my ban app. How can i reinstall it?",
    "customer_name": "Szilvia Molnar",
    "customer_email": "szilvia@example.com"
  }'

{"success":true,"ticket_id":"TKT-TEST-002","result":{"ticket_id":"TKT-TEST-002","timestamp":"2025-12-31T09:56:51.308374+00:00","triage":{"category":"Technical","subcategory":"App Installation","priority":"P3","sla_hours":72,"suggested_team":"Engineering","sentiment":"neutral","confidence":0.9},"answer_draft":{"greeting":"Dear Szilvia Molnar,","body":"I understand you've recently purchased a new phone and are looking to reinstall your bank application. Here are the general steps you can follow to reinstall an app on your phone:\n\n1. Open the app store on your device (Google Play Store for Android or App Store for iOS).\n2. Use the search function to find the bank app.\n3. Once you've found the app, click on 'Install' (for Android) or 'Get' (for iOS).\n4. After the app is installed, open it and follow the prompts to set up your account.\n\nPlease note that these are general instructions and the exact steps might vary slightly depending on your device and the specific bank app. If you encounter any issues during this process, please let us know so we can escalate this to a specialist who can provide detailed assistance.","closing":"Best Regards,\nCustomer Support Team","tone":"professional"},"citations":[],"policy_check":{"refund_promise":false,"sla_mentioned":false,"escalation_needed":false,"compliance":"passed","issues":[]}}}