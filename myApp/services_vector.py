"""
Vector embedding service for property search
"""
import openai
from django.conf import settings
from django.utils import timezone
from .models import Property, PropertyEmbedding, Organization
import json
import re


class VectorEmbeddingService:
    """Service for managing property embeddings and vector search"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.EMBEDDING_MODEL
        self.vector_dimensions = settings.VECTOR_DIMENSIONS
    
    def create_property_embedding(self, property_obj):
        """Create embeddings for a property"""
        try:
            # Build canonical document
            doc_text = self.build_property_document(property_obj)
            
            # Chunk the document
            chunks = self.chunk_text(doc_text)
            
            # Create embeddings for each chunk
            embeddings = []
            for i, chunk in enumerate(chunks):
                embedding_response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=chunk
                )
                
                embedding_vector = embedding_response.data[0].embedding
                
                # Store embedding
                PropertyEmbedding.objects.create(
                    organization=property_obj.organization,
                    property=property_obj,
                    doc_id=f"prop:{property_obj.id}",
                    chunk=i,
                    embedding=embedding_vector
                )
                
                embeddings.append(embedding_vector)
            
            return embeddings
            
        except Exception as e:
            print(f"Error creating embeddings for property {property_obj.id}: {e}")
            return []
    
    def build_property_document(self, property_obj):
        """Build a canonical document from property data"""
        parts = []
        
        # Title and location
        parts.append(f"Property: {property_obj.title}")
        parts.append(f"Location: {property_obj.city}, {property_obj.area}")
        
        # Price and details
        parts.append(f"Price: ${property_obj.price_amount:,}")
        parts.append(f"Details: {property_obj.beds} bed, {property_obj.baths} bath, {property_obj.floor_area_sqm} sqm")
        
        # Description
        if property_obj.description:
            parts.append(f"Description: {property_obj.description}")
        
        # Narrative (AI-generated analysis)
        if property_obj.narrative:
            parts.append(f"Analysis: {property_obj.narrative}")
        
        # Additional features
        features = []
        if property_obj.parking:
            features.append("Parking available")
        if property_obj.commissionable:
            features.append("Commissionable")
        if property_obj.badges:
            features.append(f"Badges: {property_obj.badges}")
        
        if features:
            parts.append(f"Features: {', '.join(features)}")
        
        # Market data
        if property_obj.estimate:
            parts.append(f"Market estimate: ${property_obj.estimate:,}")
        if property_obj.neighborhood_avg:
            parts.append(f"Neighborhood average: ${property_obj.neighborhood_avg:,}")
        
        return " | ".join(parts)
    
    def chunk_text(self, text, chunk_size=500, overlap=60):
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at word boundary
            if end < len(text):
                # Look for the last space before the end
                last_space = text.rfind(' ', start, end)
                if last_space > start + chunk_size // 2:  # Don't break too early
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def search_similar_properties(self, organization, query, limit=5):
        """Search for similar properties using vector similarity"""
        try:
            # Generate embedding for query
            query_embedding = self.client.embeddings.create(
                model=self.embedding_model,
                input=query
            ).data[0].embedding
            
            # For now, return active properties (will implement vector search with pgvector)
            # This is a placeholder - in production, you'd use pgvector's cosine similarity
            properties = Property.objects.filter(
                organization=organization,
                is_active=True
            )[:limit]
            
            return properties
            
        except Exception as e:
            print(f"Error searching properties: {e}")
            return Property.objects.filter(
                organization=organization,
                is_active=True
            )[:limit]
    
    def update_property_embeddings(self, property_obj):
        """Update embeddings for a property"""
        # Delete existing embeddings
        PropertyEmbedding.objects.filter(
            organization=property_obj.organization,
            property=property_obj
        ).delete()
        
        # Create new embeddings
        return self.create_property_embedding(property_obj)
    
    def batch_create_embeddings(self, organization, properties=None):
        """Create embeddings for multiple properties"""
        if properties is None:
            properties = Property.objects.filter(
                organization=organization,
                is_active=True
            )
        
        results = []
        for property_obj in properties:
            embeddings = self.create_property_embedding(property_obj)
            results.append({
                'property': property_obj,
                'embeddings_count': len(embeddings)
            })
        
        return results
    
    def get_property_context_for_chat(self, organization, query, limit=3):
        """Get relevant property context for chat responses"""
        properties = self.search_similar_properties(organization, query, limit)
        
        context_parts = []
        for prop in properties:
            context_parts.append(f"""
Property: {prop.title}
Location: {prop.city}, {prop.area}
Price: ${prop.price_amount:,}
Details: {prop.beds} bed, {prop.baths} bath, {prop.floor_area_sqm} sqm
Description: {prop.description[:200] if prop.description else 'No description available'}...
            """.strip())
        
        return "\n\n".join(context_parts) if context_parts else "No properties found matching your criteria."


# Global instance
vector_service = VectorEmbeddingService()
