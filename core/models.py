#!/usr/bin/env python3
"""
Core data models and types for the accident monitoring system
Provides type-safe data structures and validation
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import re

class AccidentType(Enum):
    """Types of accidents"""
    MINOR = "minor"
    MAJOR = "major"
    GENERAL = "general"
    UNKNOWN = "unknown"

class AccidentSource(Enum):
    """Source of accident information"""
    WAZE = "waze"
    TELEGRAM = "telegram"
    MANUAL = "manual"

class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSED = "processed"
    IGNORED = "ignored"
    FAILED = "failed"

@dataclass
class Coordinates:
    """Geographic coordinates"""
    latitude: float
    longitude: float
    
    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")
    
    def is_within_singapore(self) -> bool:
        """Check if coordinates are within Singapore bounds"""
        return (1.1496 <= self.latitude <= 1.4784 and 
                103.6065 <= self.longitude <= 104.0853)
    
    def distance_to(self, other: 'Coordinates') -> float:
        """Calculate distance to another coordinate in meters using Haversine formula"""
        import math
        
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371000 * c  # Earth's radius in meters

@dataclass
class Location:
    """Location information"""
    coordinates: Optional[Coordinates] = None
    address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    
    def __str__(self) -> str:
        if self.address:
            return self.address
        elif self.street and self.city:
            return f"{self.street}, {self.city}"
        elif self.street:
            return self.street
        elif self.coordinates:
            return f"{self.coordinates.latitude:.6f}, {self.coordinates.longitude:.6f}"
        else:
            return "Unknown location"
    
    @property
    def google_maps_url(self) -> Optional[str]:
        """Generate Google Maps URL"""
        if self.coordinates:
            return f"https://www.google.com/maps?q={self.coordinates.latitude},{self.coordinates.longitude}"
        return None
    
    @property
    def waze_url(self) -> Optional[str]:
        """Generate Waze navigation URL"""
        if self.coordinates:
            return f"https://www.waze.com/ul?ll={self.coordinates.latitude},{self.coordinates.longitude}&navigate=yes"
        return None

@dataclass
class AccidentReport:
    """Structured accident report"""
    id: str
    timestamp: datetime
    source: AccidentSource
    accident_type: AccidentType
    location: Location
    description: str
    
    # Optional fields
    reported_by: Optional[str] = None
    confidence: Optional[int] = None
    reliability: Optional[int] = None
    severity: Optional[str] = None
    
    # Message tracking
    original_message_id: Optional[Union[int, str]] = None
    forwarded_message_id: Optional[int] = None
    status: MessageStatus = MessageStatus.PENDING
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate accident report after creation"""
        if not self.id:
            raise ValueError("Accident ID cannot be empty")
        if not self.description:
            raise ValueError("Description cannot be empty")
    
    def to_telegram_message(self) -> str:
        """Convert to formatted Telegram message"""
        # Build message using consistent format
        message = f"Accident at {self.location}\n"
        message += f"🕐 Reported: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S SGT')}\n"
        
        if self.reported_by:
            message += f"👤 Reported by: {self.reported_by}\n"
        if self.confidence is not None:
            message += f"📈 Confidence: {self.confidence}/10\n"
        if self.reliability is not None:
            message += f"✅ Reliability: {self.reliability}/10\n"
            
        message += f"📝 {self.description}\n\n"
        
        if self.location.coordinates:
            coords = self.location.coordinates
            message += f"🗺️ [View on Google Maps ({coords.latitude:.6f}, {coords.longitude:.6f})]({self.location.google_maps_url})\n"
            message += f"🚗 [Open in Waze ({coords.latitude:.6f}, {coords.longitude:.6f})]({self.location.waze_url})"
        else:
            message += "🗺️ Location coordinates not available"
        
        return message
    
    def is_duplicate_of(self, other: 'AccidentReport', radius_meters: int = 100) -> bool:
        """Check if this report is a duplicate of another"""
        # Check location similarity
        if (self.location.coordinates and other.location.coordinates and
            self.location.coordinates.distance_to(other.location.coordinates) <= radius_meters):
            
            # Check time proximity (within 1 hour)
            time_diff = abs((self.timestamp - other.timestamp).total_seconds())
            return time_diff <= 3600
            
        return False

class AccidentParser(ABC):
    """Abstract base class for parsing accidents from different sources"""
    
    @abstractmethod
    def parse(self, data: Dict[str, Any]) -> Optional[AccidentReport]:
        """Parse accident data and return AccidentReport if valid"""
        pass
    
    @abstractmethod
    def can_parse(self, data: Dict[str, Any]) -> bool:
        """Check if this parser can handle the given data"""
        pass

class WazeAccidentParser(AccidentParser):
    """Parser for Waze accident data"""
    
    def can_parse(self, data: Dict[str, Any]) -> bool:
        """Check if data is from Waze API"""
        return (data.get('type', '').upper() in ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR'] or
                data.get('subtype', '').upper() in ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR'])
    
    def parse(self, data: Dict[str, Any]) -> Optional[AccidentReport]:
        """Parse Waze accident data"""
        if not self.can_parse(data):
            return None
            
        try:
            # Extract location
            location_data = data.get('location', {})
            coordinates = None
            if location_data.get('y') and location_data.get('x'):
                coordinates = Coordinates(
                    latitude=float(location_data['y']),
                    longitude=float(location_data['x'])
                )
                # Skip if outside Singapore
                if not coordinates.is_within_singapore():
                    return None
            
            location = Location(
                coordinates=coordinates,
                street=data.get('street', ''),
                city=data.get('city', 'Singapore')
            )
            
            # Determine accident type
            accident_type_str = data.get('type', data.get('subtype', 'ACCIDENT')).upper()
            if 'MAJOR' in accident_type_str:
                accident_type = AccidentType.MAJOR
            elif 'MINOR' in accident_type_str:
                accident_type = AccidentType.MINOR
            else:
                accident_type = AccidentType.GENERAL
            
            # Generate ID
            pub_millis = data.get('pubMillis', 0)
            if pub_millis:
                timestamp = datetime.fromtimestamp(pub_millis / 1000)
            else:
                timestamp = datetime.now()
                
            accident_id = self._generate_waze_id(location, timestamp)
            
            # Create report
            return AccidentReport(
                id=accident_id,
                timestamp=timestamp,
                source=AccidentSource.WAZE,
                accident_type=accident_type,
                location=location,
                description=f"Accident reported on {location}",
                reported_by=data.get('reportBy', 'Waze user'),
                confidence=data.get('confidence', 0),
                reliability=data.get('reliability', 0),
                metadata={
                    'waze_data': data,
                    'country': data.get('country', ''),
                    'magvar': data.get('magvar', 0)
                }
            )
            
        except Exception as e:
            # Log error but don't crash
            return None
    
    def _generate_waze_id(self, location: Location, timestamp: datetime) -> str:
        """Generate unique ID for Waze accident"""
        time_hour = timestamp.strftime('%Y%m%d_%H')
        
        if location.coordinates:
            lat, lon = location.coordinates.latitude, location.coordinates.longitude
            return f"waze_coord_{lat:.3f}_{lon:.3f}_{time_hour}"
        else:
            street = location.street or "unknown"
            city = location.city or "singapore"
            return f"waze_text_{street}_{city}_{time_hour}"

class TelegramAccidentParser(AccidentParser):
    """Parser for Telegram accident messages"""
    
    ACCIDENT_KEYWORDS = [
        'accident', 'crash', 'collision', 'breakdown', 'stalled',
        'vehicle', 'car', 'truck', 'motorcycle', 'lorry', 'bus',
        'traffic jam', 'congestion', 'blocked', 'lane closure'
    ]
    
    def can_parse(self, data: Dict[str, Any]) -> bool:
        """Check if message contains accident-related content"""
        text = data.get('text', '').lower()
        return any(keyword in text for keyword in self.ACCIDENT_KEYWORDS)
    
    def parse(self, data: Dict[str, Any]) -> Optional[AccidentReport]:
        """Parse Telegram accident message"""
        if not self.can_parse(data):
            return None
            
        try:
            text = data.get('text', '')
            message_id = data.get('message_id')
            message_date = data.get('date', 0)
            
            # Extract coordinates if present
            coordinates = self._extract_coordinates(text)
            
            # Extract location description
            location_text = self._extract_location_text(text)
            
            location = Location(
                coordinates=coordinates,
                address=location_text
            )
            
            # Skip if location mentions Malaysia (not Singapore-relevant)
            if self._contains_malaysia_keywords(text):
                return None
            
            # Generate ID
            timestamp = datetime.fromtimestamp(message_date) if message_date else datetime.now()
            accident_id = f"telegram_{message_id}_{timestamp.strftime('%Y%m%d_%H')}"
            
            return AccidentReport(
                id=accident_id,
                timestamp=timestamp,
                source=AccidentSource.TELEGRAM,
                accident_type=AccidentType.GENERAL,
                location=location,
                description=text.strip(),
                original_message_id=message_id,
                metadata={
                    'telegram_data': data,
                    'chat_id': data.get('chat', {}).get('id'),
                    'from_user': data.get('from', {}).get('username', 'unknown')
                }
            )
            
        except Exception as e:
            return None
    
    def _extract_coordinates(self, text: str) -> Optional[Coordinates]:
        """Extract coordinates from text"""
        if not text:
            return None
            
        # Pattern for decimal degrees
        pattern = r'(\d+\.\d+),\s*(\d+\.\d+)'
        match = re.search(pattern, text)
        
        if match:
            try:
                lat, lon = float(match.group(1)), float(match.group(2))
                coords = Coordinates(lat, lon)
                if coords.is_within_singapore():
                    return coords
            except (ValueError, TypeError):
                pass
                
        return None
    
    def _extract_location_text(self, text: str) -> Optional[str]:
        """Extract location description from text"""
        # Simple heuristic - look for common Singapore location patterns
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['road', 'street', 'avenue', 'highway', 'expressway']):
                return line
        
        # Fallback to first non-empty line
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Reasonable length
                return line
                
        return None
    
    def _contains_malaysia_keywords(self, text: str) -> bool:
        """Check if text is primarily about Malaysia"""
        if not text:
            return False
            
        text_lower = text.lower()
        malaysia_keywords = ['malaysia', 'kl', 'kuala lumpur', 'selangor', 'penang']
        
        # Special case for Johor - allow if mentions Singapore context
        if 'johor' in text_lower:
            singapore_context = ['singapore', 'causeway', 'woodlands', 'checkpoint', 'border']
            if any(keyword in text_lower for keyword in singapore_context):
                return False
                
        return any(keyword in text_lower for keyword in malaysia_keywords)

# Factory for creating parsers
def create_parser(source: AccidentSource) -> AccidentParser:
    """Create appropriate parser for accident source"""
    if source == AccidentSource.WAZE:
        return WazeAccidentParser()
    elif source == AccidentSource.TELEGRAM:
        return TelegramAccidentParser()
    else:
        raise ValueError(f"Unknown accident source: {source}")

if __name__ == "__main__":
    # Example usage
    
    # Test Waze parser
    waze_data = {
        'type': 'ACCIDENT',
        'location': {'x': 103.8, 'y': 1.35},
        'street': 'Orchard Road',
        'city': 'Singapore',
        'reportBy': 'TestUser',
        'confidence': 8,
        'pubMillis': int(datetime.now().timestamp() * 1000)
    }
    
    waze_parser = WazeAccidentParser()
    accident = waze_parser.parse(waze_data)
    if accident:
        print("Parsed Waze accident:")
        print(accident.to_telegram_message())
        print()
    
    # Test Telegram parser
    telegram_data = {
        'text': 'Accident on Orchard Road near Somerset MRT. Traffic jam expected.',
        'message_id': 12345,
        'date': int(datetime.now().timestamp()),
        'chat': {'id': -1001486947378}
    }
    
    telegram_parser = TelegramAccidentParser()
    accident = telegram_parser.parse(telegram_data)
    if accident:
        print("Parsed Telegram accident:")
        print(accident.to_telegram_message())