#!/usr/bin/env python3

"""
Flask Integration for AI-Scored Distress Detection
Replaces calculateDistressScore() function with comprehensive AI system
"""

import json
import os
from typing import Dict, Any, Optional
from analysis.ai_scored_distress_detector import AIScoredDistressDetector

class FlaskAIDistressIntegration:
    """
    Integration layer between Flask app and AI-scored distress detector
    Replaces the current calculateDistressScore() function
    """
    
    def __init__(self):
        self.detector = AIScoredDistressDetector()
        
    def calculate_distress_score(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        NEW FUNCTION: Replaces the old calculateDistressScore()
        
        Args:
            property_data: Dictionary containing property information with keys:
                - address1: Street address
                - address2: City, State, ZIP
                - Or parsed from existing database fields
        
        Returns:
            Dictionary with:
                - score: AI distress score (0-100)
                - confidence: AI confidence (0.0-1.0)
                - discount: Estimated discount percentage
                - explanation: Natural language explanation
                - raw_data: All collected data for transparency
        """
        
        # Extract address components
        address1, address2 = self._parse_address(property_data)
        
        if not address1 or not address2:
            return self._fallback_scoring(property_data)
        
        try:
            # Use AI-scored detector
            result = self.detector.analyze_property(address1, address2)
            
            # Format for Flask app compatibility
            return {
                'score': result['ai_analysis'].get('score', 50),
                'confidence': result['ai_analysis'].get('conf', 0.5),
                'discount': result['ai_analysis'].get('discount', '10-15%'),
                'explanation': result['ai_analysis'].get('reason', 'AI-powered distress analysis'),
                'raw_data': result['raw_data'],
                'data_sources': result['raw_data'].get('sources', []),
                'status': 'success'
            }
            
        except Exception as e:
            print(f"❌ AI distress scoring failed: {e}")
            return self._fallback_scoring(property_data)
    
    def _parse_address(self, property_data: Dict[str, Any]) -> tuple:
        """Parse address from property data"""
        
        # Method 1: Direct address components
        if 'address1' in property_data and 'address2' in property_data:
            return property_data['address1'], property_data['address2']
        
        # Method 2: Single address field
        if 'address' in property_data:
            address = property_data['address']
            parts = address.split(',')
            if len(parts) >= 2:
                return parts[0].strip(), ','.join(parts[1:]).strip()
        
        # Method 3: Database field mapping (existing app compatibility)
        address_parts = []
        
        # Street address
        if property_data.get('property_address'):
            address_parts.append(property_data['property_address'])
        elif property_data.get('street_address'):
            address_parts.append(property_data['street_address'])
            
        # City, State, ZIP
        city_state_zip = []
        if property_data.get('city'):
            city_state_zip.append(property_data['city'])
        if property_data.get('state'):
            city_state_zip.append(property_data['state'])
        if property_data.get('zip_code'):
            city_state_zip.append(property_data['zip_code'])
        
        if address_parts and city_state_zip:
            return address_parts[0], ', '.join(city_state_zip)
        
        return None, None
    
    def _fallback_scoring(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback scoring when AI analysis fails"""
        
        # Simple heuristic scoring based on available data
        score = 50  # Base score
        factors = []
        
        # Check for basic distress indicators
        if property_data.get('foreclosure_status'):
            score += 25
            factors.append("foreclosure status")
            
        if property_data.get('tax_delinquent'):
            score += 15
            factors.append("tax delinquency")
            
        if property_data.get('days_on_market', 0) > 90:
            score += 10
            factors.append("extended market time")
            
        # Price reduction
        original_price = property_data.get('original_list_price')
        current_price = property_data.get('current_list_price')
        if original_price and current_price and original_price > current_price:
            reduction = (original_price - current_price) / original_price
            if reduction > 0.1:  # 10%+ reduction
                score += 15
                factors.append("significant price reduction")
        
        score = min(100, max(0, score))  # Clamp to 0-100
        
        return {
            'score': score,
            'confidence': 0.3,  # Low confidence for fallback
            'discount': f"{score//10}-{score//8}%",
            'explanation': f"Fallback analysis based on: {', '.join(factors) if factors else 'limited data'}",
            'raw_data': property_data,
            'data_sources': ['FALLBACK'],
            'status': 'fallback'
        }
    
    def batch_score_properties(self, properties_list: list) -> list:
        """
        Score multiple properties in batch
        Useful for updating existing database records
        """
        
        results = []
        for property_data in properties_list:
            result = self.calculate_distress_score(property_data)
            result['original_property_id'] = property_data.get('id', 'unknown')
            results.append(result)
            
        return results
    
    def get_detailed_analysis(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed analysis with all raw data displayed
        For transparency in the web interface
        """
        
        result = self.calculate_distress_score(property_data)
        
        # Format raw data for web display
        raw_data = result.get('raw_data', {})
        
        formatted_data = {
            'address': raw_data.get('address', 'N/A'),
            'financial_metrics': {
                'ltv': f"{raw_data.get('ltv', 0)*100:.1f}%" if raw_data.get('ltv') else 'N/A',
                'days_on_market': raw_data.get('dom', 'N/A'),
                'median_dom': raw_data.get('medianDom', 'N/A'),
                'original_price': f"${raw_data.get('listOrig', 0):,}" if raw_data.get('listOrig') else 'N/A',
                'current_price': f"${raw_data.get('listCurr', 0):,}" if raw_data.get('listCurr') else 'N/A'
            },
            'distress_indicators': {
                'preforeclosure': raw_data.get('preFC', False),
                'tax_delinquent': raw_data.get('taxDelinq', False),
                'tax_lien_late': raw_data.get('taxLienLate', False),
                'absentee_owner': raw_data.get('absentee', False),
                'liens': raw_data.get('liens', False),
                'code_violations': raw_data.get('viol', 0)
            },
            'property_characteristics': {
                'property_age': f"{raw_data.get('propAge', 'N/A')} years" if raw_data.get('propAge') else 'N/A',
                'owner_age': raw_data.get('ownerAge', 'N/A'),
                'incomplete_construction': raw_data.get('incompleteConstruction', False),
                'critical_illness': raw_data.get('criticalIllness', False)
            },
            'risk_factors': {
                'crime_level': raw_data.get('crime', 'N/A'),
                'insurance_availability': raw_data.get('insurance', 'N/A'),
                'coastal_risk': raw_data.get('coastalRisk', 'N/A'),
                'regional_layoffs': raw_data.get('layoffs', False)
            },
            'market_conditions': {
                'absorption_rate': raw_data.get('absorp', 'N/A'),
                'rent_demand': raw_data.get('rentDemand', 'N/A'),
                'income_trend': raw_data.get('incomeTrend', 'N/A')
            }
        }
        
        return {
            'ai_analysis': result,
            'formatted_data': formatted_data,
            'data_sources': raw_data.get('sources', [])
        }

# Flask route integration example
def create_flask_routes(app, db):
    """
    Create Flask routes that use the new AI distress scoring
    Replace existing routes in your Flask app
    """
    
    ai_distress = FlaskAIDistressIntegration()
    
    @app.route('/api/analyze-distress', methods=['POST'])
    def analyze_property_distress():
        """New API endpoint for AI distress analysis"""
        try:
            property_data = request.get_json()
            result = ai_distress.calculate_distress_score(property_data)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/detailed-analysis/<property_id>')
    def get_detailed_analysis(property_id):
        """Get detailed analysis for property display"""
        try:
            # Fetch property from database
            property_data = get_property_from_db(property_id, db)
            
            if not property_data:
                return jsonify({'error': 'Property not found'}), 404
            
            result = ai_distress.get_detailed_analysis(property_data)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/batch-update-scores', methods=['POST'])
    def batch_update_distress_scores():
        """Update multiple property scores"""
        try:
            # Get properties from database
            properties = get_all_properties_from_db(db)
            
            # Batch score
            results = ai_distress.batch_score_properties(properties)
            
            # Update database
            for result in results:
                property_id = result['original_property_id']
                update_property_score_in_db(property_id, result, db)
            
            return jsonify({
                'updated': len(results),
                'status': 'success'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Database helper functions (implement based on your DB structure)
def get_property_from_db(property_id: str, db) -> Optional[Dict]:
    """Fetch property data from database"""
    # Implement based on your database structure
    pass

def get_all_properties_from_db(db) -> list:
    """Fetch all properties from database"""
    # Implement based on your database structure
    pass

def update_property_score_in_db(property_id: str, result: Dict, db):
    """Update property distress score in database"""
    # Implement based on your database structure
    pass 