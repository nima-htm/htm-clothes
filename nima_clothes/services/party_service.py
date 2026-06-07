"""
Party Service
Handles customer and supplier management
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.party import Party, PartyType


class PartyService:
    def __init__(self, session: Session):
        self.session = session
    
    def create_party(self, name: str, party_type: PartyType, phone: str = None,
                     address: str = None) -> Party:
        """Create a new party (customer/supplier)"""
        party = Party(
            name=name,
            party_type=party_type,
            phone=phone,
            address=address
        )
        
        self.session.add(party)
        self.session.commit()
        self.session.refresh(party)
        return party
    
    def get_party_by_id(self, party_id: int) -> Party:
        """Get party by ID"""
        return self.session.query(Party).filter(Party.id == party_id).first()
    
    def search_parties(self, query: str = None, party_type: PartyType = None):
        """Search parties by name or phone"""
        db_query = self.session.query(Party)
        
        if query:
            db_query = db_query.filter(
                or_(
                    Party.name.contains(query),
                    Party.phone.contains(query)
                )
            )
        
        if party_type:
            db_query = db_query.filter(Party.party_type == party_type)
        
        return db_query.all()
    
    def get_customers(self):
        """Get all customers"""
        return self.session.query(Party).filter(
            or_(
                Party.party_type == PartyType.CUSTOMER,
                Party.party_type == PartyType.BOTH
            )
        ).all()
    
    def get_suppliers(self):
        """Get all suppliers"""
        return self.session.query(Party).filter(
            or_(
                Party.party_type == PartyType.SUPPLIER,
                Party.party_type == PartyType.BOTH
            )
        ).all()
    
    def get_all_parties(self):
        """Get all parties"""
        return self.session.query(Party).all()
    
    def update_party(self, party_id: int, **kwargs) -> Party:
        """Update party information"""
        party = self.get_party_by_id(party_id)
        if not party:
            raise ValueError(f"Party with ID {party_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(party, key):
                setattr(party, value)
        
        self.session.commit()
        self.session.refresh(party)
        return party
    
    def delete_party(self, party_id: int):
        """Delete a party"""
        party = self.get_party_by_id(party_id)
        if party:
            self.session.delete(party)
            self.session.commit()
