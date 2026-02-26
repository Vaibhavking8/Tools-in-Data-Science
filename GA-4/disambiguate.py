import json
import csv
from difflib import SequenceMatcher
import re

# Cross-lingual name mappings for historical figures
CROSS_LINGUAL_NAMES = {
    'catherine': ['catherine', 'катерина', '叶卡捷琳娜', 'catherina', 'catherine de'],
    'ivan': ['ivan', 'иван', '伊凡'],
    'william': ['william', 'guillermo', 'guglielmo', '威廉'],
    'friedrich': ['friedrich', 'frederik', 'fredrick', '弗雷德里克'],
    'charles': ['charles', 'carlos', 'carlo', '卡尔', 'charles v', 'charles i'],
    'alexander': ['alexander', 'alejandro', '亚历山大', 'alexandra'],
    'henry': ['henry', 'enrique', 'enrico', '亨利', 'henri'],
    'louis': ['louis', '路易'],
    'john': ['john', 'juan', 'jean', 'johann', 'giovanni', 'joão', 'jan'],
    'philip': ['philip', 'philippe', 'filippo', '腓力', 'philipp'],
    'george': ['george', 'jorge', '乔治'],
    'frederick the great': ['frederick the great', 'friedrich der große', 'friedrich ii'],
}

def load_documents():
    """Load documents from JSONL file"""
    documents = []
    with open('documents.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            documents.append(json.loads(line.strip()))
    return documents

def load_entities():
    """Load entity reference data from CSV"""
    entities = {}
    with open('entity_reference.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse era into year range
            era = row['era']
            years = []
            if '–' in era and 'BC' not in era:
                try:
                    start, end = era.split('–')
                    years = [int(start), int(end)]
                except:
                    years = []
            elif 'BC' in era:
                # Handle BC dates
                try:
                    parts = era.replace('–', ' ').replace('BC', '').strip().split()
                    if len(parts) >= 2:
                        years = [-int(parts[0]), -int(parts[1])]
                except:
                    years = []
            
            entities[row['entity_id']] = {
                'canonical_name': row['canonical_name'],
                'role': row['role'],
                'era': era,
                'region': row['region'],
                'years': years
            }
    return entities

def extract_base_name(name):
    """Extract base name from mentioned_name"""
    # Remove titles, numbers, etc.
    name = re.sub(r'\s+\d+$', '', name)  # Remove trailing numbers
    name = re.sub(r'\s+(I{1,3}|IV|V|VI|VII|VIII|IX|X|XI|XII)$', '', name)  # Remove Roman numerals
    name = re.sub(r'\s+de\s+.*$', '', name, flags=re.IGNORECASE)  # Remove "de" part
    name = re.sub(r'\s+the\s+.*$', '', name, flags=re.IGNORECASE)  # Remove "the" part
    name = re.sub(r'[^\w\s\-]', '', name)  # Remove special characters
    return name.strip().lower()

def get_matching_score(mentioned_name, canonical_name, document_year, entity_years, source_region, entity_region):
    """Calculate matching score between mentioned name and canonical name"""
    base_mentioned = extract_base_name(mentioned_name)
    base_canonical = extract_base_name(canonical_name)
    
    # Name similarity using sequence matching
    name_ratio = SequenceMatcher(None, base_mentioned, base_canonical).ratio()
    
    # Check cross-lingual mappings
    cross_lingual_bonus = 0
    for key, variations in CROSS_LINGUAL_NAMES.items():
        if any(v in base_mentioned for v in variations):
            if any(v in base_canonical for v in variations):
                cross_lingual_bonus = 0.3
                break
    
    # Year matching (if entity has year range)
    year_bonus = 0
    if entity_years and len(entity_years) == 2:
        start_year, end_year = entity_years
        # Check if document year is within or close to entity's era
        if start_year <= document_year <= end_year:
            year_bonus = 0.4
        elif abs(document_year - start_year) <= 30 or abs(document_year - end_year) <= 30:
            year_bonus = 0.2
    
    # Region matching
    region_bonus = 0
    if source_region.lower() in entity_region.lower() or entity_region.lower() in source_region.lower():
        region_bonus = 0.3
    
    total_score = name_ratio + cross_lingual_bonus + year_bonus + region_bonus
    
    return total_score

def disambiguate_entity(document, entities):
    """Find the best matching entity for a document"""
    mentioned_name = document['mentioned_name']
    doc_year = document['year']
    source_region = document['source_region']
    
    best_entity_id = None
    best_score = -1
    
    for entity_id, entity_info in entities.items():
        score = get_matching_score(
            mentioned_name,
            entity_info['canonical_name'],
            doc_year,
            entity_info['years'],
            source_region,
            entity_info['region']
        )
        
        if score > best_score:
            best_score = score
            best_entity_id = entity_id
    
    return best_entity_id if best_score > 0 else 'E001'

def main():
    # Load data
    documents = load_documents()
    entities = load_entities()
    
    # Disambiguate and create output
    results = []
    for doc in documents:
        entity_id = disambiguate_entity(doc, entities)
        results.append({
            'doc_id': doc['doc_id'],
            'entity_id': entity_id
        })
    
    # Write output CSV
    with open('output.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['doc_id', 'entity_id'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Successfully disambiguated {len(results)} documents")
    print("Output saved to output.csv")

if __name__ == '__main__':
    main()
