"""
Biological Classifier Model

Full taxonomic hierarchy classification:
Kingdom → Phylum → Class → Order → Family → Genus → Species
"""
from typing import Any, Dict, Optional
import numpy as np

from ml.registry import DetectionType, model_registry


class BiologicalClassifier:
    """Classifier for full biological taxonomy."""
    
    def __init__(self):
        self.detection_type = DetectionType.BIOLOGICAL
        self.config = model_registry.get_config(self.detection_type)
        self._model = None
    
    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Predict full taxonomic hierarchy.
        
        Args:
            image: Preprocessed numpy array
            
        Returns:
            Prediction result with full hierarchy
        """
        self._model = model_registry.load_model(self.detection_type)
        
        if self._model is None:
            return self._mock_predict()
        
        # Real prediction logic would go here
        predictions = self._model.predict(image)
        return self._format_hierarchy(predictions)
    
    def _format_hierarchy(self, predictions: np.ndarray) -> Dict[str, Any]:
        """Format predictions into taxonomic hierarchy."""
        # This would decode multi-output model predictions
        return {
            "hierarchy": {
                "Kingdom": "Animalia",
                "Phylum": "Chordata",
                "Class": "Mammalia",
                "Order": "Carnivora",
                "Family": "Felidae",
                "Genus": "Panthera",
                "Species": "Panthera leo"
            },
            "confidence": 0.92,
            "formatted": "Animalia → Chordata → Mammalia → Carnivora → Felidae → Panthera → Panthera leo"
        }
    
    def _mock_predict(self) -> Dict[str, Any]:
        """Generate mock biological classification."""
        import random
        
        # Sample taxonomies
        taxonomies = [
            {
                "Kingdom": "Animalia",
                "Phylum": "Chordata", 
                "Class": "Mammalia",
                "Order": "Carnivora",
                "Family": "Felidae",
                "Genus": "Panthera",
                "Species": "Panthera leo"
            },
            {
                "Kingdom": "Animalia",
                "Phylum": "Chordata",
                "Class": "Aves",
                "Order": "Passeriformes",
                "Family": "Corvidae",
                "Genus": "Corvus",
                "Species": "Corvus corax"
            },
            {
                "Kingdom": "Plantae",
                "Phylum": "Magnoliophyta",
                "Class": "Magnoliopsida",
                "Order": "Sapindales",
                "Family": "Rutaceae",
                "Genus": "Citrus",
                "Species": "Citrus sinensis"
            }
        ]
        
        taxonomy = random.choice(taxonomies)
        confidence = random.uniform(0.80, 0.98)
        
        formatted = " → ".join(taxonomy.values())
        
        return {
            "hierarchy": taxonomy,
            "confidence": round(confidence, 4),
            "formatted": formatted,
            "is_mock": True
        }
