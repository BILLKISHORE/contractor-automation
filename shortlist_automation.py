import os
from pyairtable import Api
from dotenv import load_dotenv
import json

load_dotenv()

class ShortlistAutomation:
    def __init__(self):
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.tier_1_companies = ['Google', 'Meta', 'OpenAI', 'Microsoft', 'Amazon', 'Apple', 'Netflix']
        self.approved_locations = ['United States', 'Canada', 'United Kingdom', 'Germany', 'India', 'US', 'UK']
    
    def evaluate_candidate(self, applicant_id):
        """Evaluate candidate against shortlist criteria"""
  
        applicants_table = self.api.table(self.base_id, 'Applicants')
        applicant_record = applicants_table.get(applicant_id)
        
        if not applicant_record or 'Compressed JSON' not in applicant_record['fields']:
            return False, "No data found"
        
        json_data = json.loads(applicant_record['fields']['Compressed JSON'])
       
        experience_pass, exp_reason = self._check_experience_criteria(json_data.get('experience', []))
        compensation_pass, comp_reason = self._check_compensation_criteria(json_data.get('salary', {}))
        location_pass, loc_reason = self._check_location_criteria(json_data.get('personal', {}))
        
        
        passes_all = experience_pass and compensation_pass and location_pass
        
        reason_parts = []
        reason_parts.append(f"   Experience: {exp_reason}" if experience_pass else f"   Experience: {exp_reason}")
        reason_parts.append(f"   Compensation: {comp_reason}" if compensation_pass else f"   Compensation: {comp_reason}")
        reason_parts.append(f"   Location: {loc_reason}" if location_pass else f"   Location: {loc_reason}")
        
        full_reason = "\n".join(reason_parts)
        
        if passes_all:
            self._create_shortlisted_lead(applicant_id, json_data, full_reason)
            print(f"   {json_data['personal']['name']} has been shortlisted!")
        else:
            print(f"   {json_data['personal'].get('name', 'Applicant')} did not meet criteria")
            
        return passes_all, full_reason
    
    def _check_experience_criteria(self, experience_data):
        """4 years total OR worked at Tier-1 company"""
        total_jobs = len(experience_data)
        has_tier1 = any(exp.get('company') in self.tier_1_companies for exp in experience_data)
        
        if total_jobs >= 4:
            return True, f"Has {total_jobs}+ job experiences"
        elif has_tier1:
            tier1_companies = [exp['company'] for exp in experience_data if exp.get('company') in self.tier_1_companies]
            return True, f"Worked at Tier-1 company: {', '.join(tier1_companies)}"
        else:
            return False, f"Only {total_jobs} job experiences, no Tier-1 companies"
    
    def _check_compensation_criteria(self, salary_data):
        """Preferred Rate $100/hr AND Availability 20hrs/week"""
        preferred_rate = salary_data.get('preferred_rate', float('inf'))
        availability = salary_data.get('availability', 0)
        
        rate_ok = preferred_rate <= 100
        availability_ok = availability >= 20
        
        if rate_ok and availability_ok:
            return True, f"Rate ${preferred_rate}/hr, {availability}hrs/week available"
        else:
            issues = []
            if not rate_ok:
                issues.append(f"Rate too high (${preferred_rate})")
            if not availability_ok:
                issues.append(f"Low availability ({availability}hrs)")
            return False, ", ".join(issues)
    
    def _check_location_criteria(self, personal_data):
        """Must be in US, Canada, UK, Germany, or India, US, UK"""
        location = personal_data.get('location', '').strip()
        
        for approved_loc in self.approved_locations:
            if approved_loc.lower() in location.lower():
                return True, f"Located in {location}"
        
        return False, f"Location '{location}' not in approved regions"
    
    def _create_shortlisted_lead(self, applicant_id, json_data, reason):
        """Create shortlisted lead record"""
        shortlisted_table = self.api.table(self.base_id, 'Shortlisted Leads')
        
        shortlisted_table.create({
            'Applicant': [applicant_id],
            'Compressed JSON': json.dumps(json_data, indent=2),
            'Score Reason': reason
        })
        
        applicants_table = self.api.table(self.base_id, 'Applicants')
        applicants_table.update(applicant_id, {
            'Shortlist Status': 'Shortlisted'
        })

if __name__ == "__main__":
    automation = ShortlistAutomation()
    passes, reason = automation.evaluate_candidate("rec123456789")
    print(f"Shortlist Result: {passes}")
    print(f"Details:\n{reason}")
