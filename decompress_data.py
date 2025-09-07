import os
from pyairtable import Api
from dotenv import load_dotenv
import json

load_dotenv()

class AirtableDecompressor:
    def __init__(self):
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        
    def decompress_from_json(self, applicant_id):
        """Decompress JSON back to normalized tables"""
        
        applicants_table = self.api.table(self.base_id, 'Applicants')
        applicant_record = applicants_table.get(applicant_id)
        
        if not applicant_record or 'Compressed JSON' not in applicant_record['fields']:
            raise ValueError("No compressed JSON found for this applicant")
        
        json_data = json.loads(applicant_record['fields']['Compressed JSON'])
        

        self._update_personal_details(applicant_id, json_data.get('personal', {}))
        

        self._update_work_experience(applicant_id, json_data.get('experience', []))
        

        self._update_salary_preferences(applicant_id, json_data.get('salary', {}))
        
        print(f"   Decompressed data for applicant {applicant_id}")
        
    def _update_personal_details(self, applicant_id, personal_data):
        """Update or create personal details record"""
        personal_table = self.api.table(self.base_id, 'Personal Details')
        existing_records = personal_table.all(formula=f"{{Applicant ID}} = {applicant_id}")
        
        record_data = {
            'Applicant ID': [applicant_id],
            'Full Name': personal_data.get('name', ''),
            'Email': personal_data.get('email', ''),
            'Location': personal_data.get('location', ''),
            'LinkedIn': personal_data.get('linkedin', '')
        }
        
        if existing_records:
            personal_table.update(existing_records[0]['id'], record_data)
        else:
            personal_table.create(record_data)
    
    def _update_work_experience(self, applicant_id, experience_data):
        """Update or create work experience records"""
        experience_table = self.api.table(self.base_id, 'Work Experience')
        existing_records = experience_table.all(formula=f"{{Applicant ID}} = {applicant_id}")
        

        for record in existing_records:
            experience_table.delete(record['id'])
            

        for exp in experience_data:
            record_data = {
                'Applicant ID': [applicant_id],
                'Company': exp.get('company', ''),
                'Title': exp.get('title', ''),
                'Start Date': exp.get('start_date', ''),
                'End Date': exp.get('end_date', ''),
                'Technologies': exp.get('technologies', [])
            }
            experience_table.create(record_data)

    def _update_salary_preferences(self, applicant_id, salary_data):
        """Update or create salary preferences record"""
        salary_table = self.api.table(self.base_id, 'Salary Preferences')
        existing_records = salary_table.all(formula=f"{{Applicant ID}} = {applicant_id}")
        
        record_data = {
            'Applicant ID': [applicant_id],
            'Preferred Rate': salary_data.get('preferred_rate', 0),
            'Minimum Rate': salary_data.get('minimum_rate', 0),
            'Currency': salary_data.get('currency', 'USD'),
            'Availability Hours per Week': salary_data.get('availability', 0)
        }

        if existing_records:
            salary_table.update(existing_records[0]['id'], record_data)
        else:
            salary_table.create(record_data)


if __name__ == "__main__":
    decompressor = AirtableDecompressor()

    decompressor.decompress_from_json("rec123456789")
    print("   Decompression complete!")
