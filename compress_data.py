import os
from pyairtable import Api
from dotenv import load_dotenv
import json

load_dotenv()

class AirtableCompressor:
    def __init__(self):
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        
    def get_applicant_data(self, applicant_id):
        """Gather all data for a specific applicant"""
    
        personal_table = self.api.table(self.base_id, 'Personal Details')
        personal_records = personal_table.all(formula=f"{{Applicant ID}} = {applicant_id}")
        
        experience_table = self.api.table(self.base_id, 'Work Experience')
        experience_records = experience_table.all(formula=f"{{Applicant ID}} = {applicant_id}")
        
        salary_table = self.api.table(self.base_id, 'Salary Preferences')
        salary_records = salary_table.all(formula=f"{{Applicant ID}} = {applicant_id}")
        
        return personal_records, experience_records, salary_records
    
    def compress_to_json(self, applicant_id):
        """Compress applicant data into single JSON object"""
        personal_records, experience_records, salary_records = self.get_applicant_data(applicant_id)
        
        compressed_data = {
            "personal": {},
            "experience": [],
            "salary": {}
        }
        
        if personal_records:
            personal = personal_records[0]['fields']
            compressed_data["personal"] = {
                "name": personal.get('Full Name', ''),
                "email": personal.get('Email', ''),
                "location": personal.get('Location', ''),
                "linkedin": personal.get('LinkedIn', '')
            }
        
        for exp in experience_records:
            exp_data = exp['fields']
            compressed_data["experience"].append({
                "company": exp_data.get('Company', ''),
                "title": exp_data.get('Title', ''),
                "start_date": exp_data.get('Start Date', ''),
                "end_date": exp_data.get('End Date', ''),
                "technologies": exp_data.get('Technologies', [])
            })
        
        if salary_records:
            salary = salary_records[0]['fields']
            compressed_data["salary"] = {
                "preferred_rate": salary.get('Preferred Rate', 0),
                "minimum_rate": salary.get('Minimum Rate', 0),
                "currency": salary.get('Currency', 'USD'),
                "availability": salary.get('Availability Hours per Week', 0)
            }
        
        applicants_table = self.api.table(self.base_id, 'Applicants')
        applicants_table.update(applicant_id, {
            'Compressed JSON': json.dumps(compressed_data, indent=2)
        })
        
        print(f"   Compressed data for applicant {applicant_id}")
        return compressed_data

if __name__ == "__main__":
    compressor = AirtableCompressor()
    result = compressor.compress_to_json("rec123456789")
    print("Compression complete!")
