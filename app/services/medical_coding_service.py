"""
Medical Coding Service - Multi-code detection and billing intelligence
Handles anesthesia codes, modifiers, and comprehensive medical billing
"""

from typing import Dict, List, Optional, Union
import re


class MedicalCodingService:
    """
    Advanced medical coding service for comprehensive billing
    Detects multiple CPT codes, anesthesia codes, and modifiers
    """
    
    def __init__(self, billing):
        self.billing = billing
        
        # CPT to Anesthesia Code Mapping (common procedures)
        self.cpt_anesthesia_map = {
            # Knee procedures
            '27447': '00402',  # Total knee arthroplasty -> Anesthesia for procedures on knee
            '27446': '00402',  # Partial knee replacement
            '27440': '00402',  # Total knee arthroplasty with patella
            '29881': '00400',  # Arthroscopy, knee -> Anesthesia for procedures on knee
            '29882': '00400',  # Arthroscopy with meniscectomy
            
            # Hip procedures  
            '27130': '01200',  # Total hip arthroplasty -> Anesthesia for procedures on hip
            '27132': '01200',  # Conversion to total hip arthroplasty
            '27134': '01200',  # Revision of total hip arthroplasty
            
            # Shoulder procedures
            '23472': '01630',  # Total shoulder arthroplasty -> Anesthesia for shoulder
            '29827': '01630',  # Arthroscopy, shoulder
            
            # Spine procedures
            '22558': '00600',  # Arthrodesis, anterior interbody -> Anesthesia for spine
            '22612': '00600',  # Arthrodesis, posterior
            
            # Hand/Wrist procedures
            '25332': '01810',  # Arthroplasty, wrist -> Anesthesia for forearm/wrist/hand
        }
        
        # Anatomical modifier mapping
        self.anatomical_modifiers = {
            'right': 'RT',
            'left': 'LT', 
            'bilateral': '50',
            'multiple': '51',
            'reduced': '52',
            'discontinued': '53'
        }
        
        # Medical specialties for context
        self.medical_specialties = {
            'orthopedic': ['knee', 'hip', 'shoulder', 'spine', 'joint', 'bone'],
            'cardiovascular': ['heart', 'cardiac', 'vessel', 'artery', 'vein'],
            'neurological': ['brain', 'nerve', 'spinal', 'neural'],
            'gastroenterology': ['stomach', 'intestine', 'colon', 'liver'],
            'gynecology': ['uterus', 'ovary', 'cervix', 'fallopian']
        }
    
    def detect_comprehensive_codes(self, primary_cpt_codes: List[Dict], 
                                 ai_extracted_text: str, 
                                 original_medical_note: str) -> Dict:
        """
        Comprehensive multi-code detection for complete medical billing
        
        Args:
            primary_cpt_codes: List of detected primary CPT codes with similarity scores
            ai_extracted_text: AI-processed medical text
            original_medical_note: Original raw medical note
            
        Returns:
            Dict containing all detected codes and modifiers
        """
        try:
            result = {
                'primary_codes': primary_cpt_codes,
                'anesthesia_codes': [],
                'modifiers': [],
                'related_codes': [],
                'coding_confidence': self._calculate_confidence(primary_cpt_codes),
                'medical_specialty': self._detect_specialty(ai_extracted_text),
                'billing_summary': {}
            }
            
            # Process each primary CPT code
            for cpt_result in primary_cpt_codes:
                cpt_code = cpt_result.get('cpt_code', '')
                
                # 1. Detect anesthesia codes
                anesthesia_codes = self._detect_anesthesia_codes(cpt_code, ai_extracted_text)
                result['anesthesia_codes'].extend(anesthesia_codes)
                
                # 2. Detect anatomical modifiers
                modifiers = self._detect_modifiers(ai_extracted_text, original_medical_note)
                result['modifiers'].extend(modifiers)
                
                # 3. Detect related/secondary codes
                related_codes = self._detect_related_codes(cpt_code, ai_extracted_text)
                result['related_codes'].extend(related_codes)
            
            # Remove duplicates
            result['anesthesia_codes'] = self._remove_duplicate_codes(result['anesthesia_codes'])
            result['modifiers'] = self._remove_duplicate_modifiers(result['modifiers'])
            result['related_codes'] = self._remove_duplicate_codes(result['related_codes'])
            
            # Generate billing summary
            result['billing_summary'] = self._generate_billing_summary(result)
            
            print(f"🏥 Multi-code detection completed:")
            print(f"   Primary codes: {len(result['primary_codes'])}")
            print(f"   Anesthesia codes: {len(result['anesthesia_codes'])}")
            print(f"   Modifiers: {len(result['modifiers'])}")
            print(f"   Related codes: {len(result['related_codes'])}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in comprehensive code detection: {e}")
            return {
                'primary_codes': primary_cpt_codes,
                'anesthesia_codes': [],
                'modifiers': [],
                'related_codes': [],
                'coding_confidence': 'low',
                'error': str(e)
            }
    
    def _detect_anesthesia_codes(self, primary_cpt: str, medical_text: str) -> List[Dict]:
        """Detect anesthesia codes based on primary CPT and procedure context"""
        anesthesia_codes = []
        
        # Direct CPT to anesthesia mapping
        if primary_cpt in self.cpt_anesthesia_map:
            anesthesia_code = self.cpt_anesthesia_map[primary_cpt]
            anesthesia_codes.append({
                'code': anesthesia_code,
                'description': self._get_anesthesia_description(anesthesia_code),
                'type': 'anesthesia',
                'similarity': 0.98,  # High confidence for mapped codes
                'reason': f'Standard anesthesia for CPT {primary_cpt}'
            })
        
        # Context-based anesthesia detection
        lower_text = medical_text.lower()
        
        if any(term in lower_text for term in ['general anesthesia', 'under general']):
            if not anesthesia_codes:  # Only add if not already detected
                # Infer anesthesia based on procedure complexity
                if any(term in lower_text for term in ['arthroplasty', 'replacement', 'major']):
                    anesthesia_codes.append({
                        'code': '00400',  # Default for major orthopedic
                        'description': 'Anesthesia for procedures on the knee',
                        'type': 'anesthesia',
                        'similarity': 0.85,
                        'reason': 'General anesthesia indicated for major procedure'
                    })
        
        return anesthesia_codes
    
    def _detect_modifiers(self, medical_text: str, original_note: str) -> List[Dict]:
        """Detect anatomical and procedural modifiers"""
        modifiers = []
        combined_text = (medical_text + " " + original_note).lower()
        
        # Anatomical laterality detection
        if 'right' in combined_text and 'left' not in combined_text:
            modifiers.append({
                'code': 'RT',
                'description': 'Right side',
                'type': 'anatomical',
                'reason': 'Right laterality identified'
            })
        elif 'left' in combined_text and 'right' not in combined_text:
            modifiers.append({
                'code': 'LT', 
                'description': 'Left side',
                'type': 'anatomical',
                'reason': 'Left laterality identified'
            })
        elif 'bilateral' in combined_text or ('right' in combined_text and 'left' in combined_text):
            modifiers.append({
                'code': '50',
                'description': 'Bilateral procedure',
                'type': 'anatomical', 
                'reason': 'Bilateral procedure identified'
            })
        
        # Procedural modifiers
        if any(term in combined_text for term in ['multiple procedures', 'additional procedure']):
            modifiers.append({
                'code': '51',
                'description': 'Multiple procedures',
                'type': 'procedural',
                'reason': 'Multiple procedures indicated'
            })
        
        if any(term in combined_text for term in ['reduced services', 'partial procedure']):
            modifiers.append({
                'code': '52',
                'description': 'Reduced services', 
                'type': 'procedural',
                'reason': 'Reduced services indicated'
            })
        
        return modifiers
    
    def _detect_related_codes(self, primary_cpt: str, medical_text: str) -> List[Dict]:
        """Detect related diagnostic or ancillary codes"""
        related_codes = []
        lower_text = medical_text.lower()
        
        # Common diagnostic codes based on procedures
        diagnostic_mappings = {
            '27447': [  # Total knee arthroplasty
                {'code': 'M17.9', 'description': 'Osteoarthritis of knee, unspecified', 'type': 'diagnosis'},
                {'code': 'Z96.651', 'description': 'Presence of right artificial knee joint', 'type': 'status'}
            ],
            '27130': [  # Total hip arthroplasty
                {'code': 'M16.9', 'description': 'Osteoarthritis of hip, unspecified', 'type': 'diagnosis'},
                {'code': 'Z96.641', 'description': 'Presence of right artificial hip joint', 'type': 'status'}
            ]
        }
        
        if primary_cpt in diagnostic_mappings:
            for related in diagnostic_mappings[primary_cpt]:
                # Adjust laterality for status codes
                if 'right' in lower_text and 'Z96' in related['code']:
                    related_codes.append({
                        **related,
                        'similarity': 0.95,
                        'reason': f'Standard diagnosis for {primary_cpt}'
                    })
                elif 'left' in lower_text and 'Z96' in related['code']:
                    # Adjust code for left side
                    left_code = related['code'].replace('641', '642')  # Right to left
                    related_codes.append({
                        'code': left_code,
                        'description': related['description'].replace('right', 'left'),
                        'type': related['type'],
                        'similarity': 0.95,
                        'reason': f'Standard diagnosis for {primary_cpt} - left side'
                    })
                else:
                    related_codes.append({
                        **related,
                        'similarity': 0.90,
                        'reason': f'Standard diagnosis for {primary_cpt}'
                    })
        
        return related_codes
    
    def _detect_specialty(self, medical_text: str) -> str:
        """Detect medical specialty based on procedure context"""
        lower_text = medical_text.lower()
        
        for specialty, keywords in self.medical_specialties.items():
            if any(keyword in lower_text for keyword in keywords):
                return specialty
        
        return 'general'
    
    def _calculate_confidence(self, primary_codes: List[Dict]) -> str:
        """Calculate overall coding confidence based on primary code similarities"""
        if not primary_codes:
            return 'low'
        
        avg_similarity = sum(code.get('similarity', 0) for code in primary_codes) / len(primary_codes)
        
        if avg_similarity >= 0.9:
            return 'high'
        elif avg_similarity >= 0.7:
            return 'medium' 
        else:
            return 'low'
    
    def _get_anesthesia_description(self, anesthesia_code: str) -> str:
        """Get description for anesthesia codes"""
        descriptions = {
            '00400': 'Anesthesia for procedures on the knee',
            '00402': 'Anesthesia for procedures on the knee; total knee arthroplasty',
            '01200': 'Anesthesia for procedures on hip joint',
            '01630': 'Anesthesia for procedures on shoulder and axilla',
            '00600': 'Anesthesia for procedures on cervical spine and cord',
            '01810': 'Anesthesia for procedures on forearm, wrist, and hand'
        }
        return descriptions.get(anesthesia_code, 'Anesthesia procedure')
    
    def _remove_duplicate_codes(self, codes: List[Dict]) -> List[Dict]:
        """Remove duplicate codes from list"""
        seen_codes = set()
        unique_codes = []
        
        for code_dict in codes:
            code = code_dict.get('code', '')
            if code not in seen_codes:
                seen_codes.add(code)
                unique_codes.append(code_dict)
        
        return unique_codes
    
    def _remove_duplicate_modifiers(self, modifiers: List[Dict]) -> List[Dict]:
        """Remove duplicate modifiers from list"""
        seen_modifiers = set()
        unique_modifiers = []
        
        for modifier_dict in modifiers:
            modifier = modifier_dict.get('code', '')
            if modifier not in seen_modifiers:
                seen_modifiers.add(modifier)
                unique_modifiers.append(modifier_dict)
        
        return unique_modifiers
    
    def _generate_billing_summary(self, result: Dict) -> Dict:
        """Generate comprehensive billing summary"""
        return {
            'total_codes': len(result['primary_codes']) + len(result['anesthesia_codes']) + len(result['related_codes']),
            'has_modifiers': len(result['modifiers']) > 0,
            'has_anesthesia': len(result['anesthesia_codes']) > 0,
            'complexity': 'complex' if len(result['primary_codes']) + len(result['related_codes']) > 2 else 'simple',
            'specialty': result.get('medical_specialty', 'general'),
            'billing_confidence': result.get('coding_confidence', 'medium')
        }