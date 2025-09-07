import os
from pyairtable import Api
from dotenv import load_dotenv
import json
import time
import logging
import openai

load_dotenv()

class LLMEvaluator:
    def __init__(self):
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def evaluate_applicant(self, applicant_id, max_retries=3):
        """Evaluate applicant using LLM with retry logic"""
        
        applicants_table = self.api.table(self.base_id, 'Applicants')
        applicant_record = applicants_table.get(applicant_id)
        
        if not applicant_record or 'Compressed JSON' not in applicant_record['fields']:
            self.logger.error(f"No compressed JSON found for applicant {applicant_id}")
            return None
        
        json_data = applicant_record['fields']['Compressed JSON']
        
        for attempt in range(max_retries):
            try:
                response = self._call_llm(json_data)
                
                if response:
                    parsed_response = self._parse_llm_response(response)
                    
                    applicants_table.update(applicant_id, {
                        'LLM Summary': parsed_response['summary'],
                        'LLM Score': parsed_response['score'],
                        'LLM Follow-Ups': parsed_response['follow_ups']
                    })
                    
                    self.logger.info(f"   Successfully evaluated applicant {applicant_id}")
                    print(f"   LLM Evaluation Complete - Score: {parsed_response['score']}/10")
                    return parsed_response
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        self.logger.error(f"   Failed to evaluate applicant {applicant_id} after {max_retries} attempts")
        return None
    
    def _call_llm(self, json_data):
        """Make API call to OpenAI"""
        
        prompt = f"""You are a recruiting analyst. Given this JSON applicant profile, do four things:

1. Provide a concise 75-word summary.
2. Rate overall candidate quality from 1-10 (higher is better).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps.

Applicant Profile:
{json_data}

Return exactly in this format:
Summary: <your 75-word summary here>
Score: <integer from 1-10>
Issues: <comma-separated list or 'None'>
Follow-Ups: <bullet list with • symbols>"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _parse_llm_response(self, response_text):
        """Parse structured LLM response"""
        lines = response_text.strip().split('\n')
        
        parsed = {
            'summary': '',
            'score': 5,
            'issues': 'None',
            'follow_ups': ''
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Summary:'):
                parsed['summary'] = line.replace('Summary:', '').strip()
            elif line.startswith('Score:'):
                try:
                    score_text = line.replace('Score:', '').strip()
                    parsed['score'] = int(score_text)
                except ValueError:
                    parsed['score'] = 5
            elif line.startswith('Issues:'):
                parsed['issues'] = line.replace('Issues:', '').strip()
            elif line.startswith('Follow-Ups:'):
                current_section = 'follow_ups'
                follow_up_text = line.replace('Follow-Ups:', '').strip()
                if follow_up_text:
                    parsed['follow_ups'] = follow_up_text
            elif current_section == 'follow_ups' and line.startswith('•'):
                if parsed['follow_ups']:
                    parsed['follow_ups'] += '\n' + line
                else:
                    parsed['follow_ups'] = line
        
        return parsed

if __name__ == "__main__":
    evaluator = LLMEvaluator()
    result = evaluator.evaluate_applicant("rec123456789")
    if result:
        print(f"Summary: {result['summary']}")
        print(f"Score: {result['score']}/10")
        print(f"Issues: {result['issues']}")
        print(f"Follow-ups:\n{result['follow_ups']}")
