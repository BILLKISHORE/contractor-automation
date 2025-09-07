from compress_data import AirtableCompressor
from shortlist_automation import ShortlistAutomation
from llm_evaluation import LLMEvaluator
import sys

def process_applicant(applicant_id):
    """Complete processing pipeline for an applicant"""
    
    print(f"\n Starting processing for applicant:
