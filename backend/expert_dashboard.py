"""
Complyo Expert Dashboard - Professional Case Management System
Handles expert consultations, case tracking, and expert workflow management
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsultationStatus(Enum):
    REQUESTED = "requested"
    ASSIGNED = "assigned"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FOLLOW_UP_REQUIRED = "follow_up_required"

class ConsultationType(Enum):
    INITIAL_CONSULTATION = "initial_consultation"
    COMPLIANCE_REVIEW = "compliance_review"
    LEGAL_ADVICE = "legal_advice"
    TECHNICAL_SUPPORT = "technical_support"
    DOCUMENT_REVIEW = "document_review"
    EMERGENCY_CONSULTATION = "emergency_consultation"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class ExpertSpecialty(Enum):
    GDPR_COMPLIANCE = "gdpr_compliance"
    PRIVACY_LAW = "privacy_law"
    WEBSITE_LAW = "website_law"
    TECHNICAL_COMPLIANCE = "technical_compliance"
    ACCESSIBILITY = "accessibility"
    COOKIE_LAW = "cookie_law"
    ECOMMERCE_LAW = "ecommerce_law"

@dataclass
class Expert:
    """Expert profile"""
    expert_id: str
    email: str
    first_name: str
    last_name: str
    title: str
    specialties: List[ExpertSpecialty]
    languages: List[str]
    is_available: bool = True
    hourly_rate: float = 200.0
    timezone: str = "Europe/Berlin"
    bio: Optional[str] = None
    certifications: List[str] = None
    years_experience: int = 5
    rating: float = 5.0
    total_consultations: int = 0
    availability_schedule: Dict[str, List[str]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.certifications is None:
            self.certifications = []
        if self.availability_schedule is None:
            self.availability_schedule = {
                "monday": ["09:00", "17:00"],
                "tuesday": ["09:00", "17:00"], 
                "wednesday": ["09:00", "17:00"],
                "thursday": ["09:00", "17:00"],
                "friday": ["09:00", "17:00"]
            }

@dataclass
class ConsultationRequest:
    """Consultation request from client"""
    request_id: str
    client_id: str
    consultation_type: ConsultationType
    title: str
    description: str
    priority: Priority
    website_urls: List[str]
    preferred_language: str = "de"
    preferred_datetime: Optional[datetime] = None
    budget_range: Optional[str] = None
    urgency_reason: Optional[str] = None
    attachments: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.attachments is None:
            self.attachments = []

@dataclass 
class Consultation:
    """Active consultation case"""
    consultation_id: str
    client_id: str
    expert_id: Optional[str]
    request: ConsultationRequest
    status: ConsultationStatus
    scheduled_datetime: Optional[datetime] = None
    duration_minutes: int = 60
    meeting_link: Optional[str] = None
    meeting_password: Optional[str] = None
    consultation_notes: Optional[str] = None
    expert_recommendations: List[str] = None
    follow_up_tasks: List[Dict[str, Any]] = None
    follow_up_date: Optional[datetime] = None
    completion_summary: Optional[str] = None
    client_rating: Optional[int] = None
    client_feedback: Optional[str] = None
    total_cost: float = 0.0
    billing_status: str = "pending"
    created_at: datetime = None
    updated_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.expert_recommendations is None:
            self.expert_recommendations = []
        if self.follow_up_tasks is None:
            self.follow_up_tasks = []

@dataclass
class ExpertAvailability:
    """Expert availability slot"""
    expert_id: str
    date: datetime
    start_time: str
    end_time: str
    is_available: bool = True
    consultation_id: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class CaseNote:
    """Case progress note"""
    note_id: str
    consultation_id: str
    author_id: str
    author_type: str  # "expert" or "client" or "admin"
    content: str
    note_type: str = "progress"  # progress, recommendation, technical, billing
    is_private: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ExpertDashboardManager:
    """Expert dashboard and case management system"""
    
    def __init__(self):
        """Initialize expert dashboard manager"""
        
        # Storage (in production: use database)
        self.experts: Dict[str, Expert] = {}
        self.consultation_requests: Dict[str, ConsultationRequest] = {}
        self.consultations: Dict[str, Consultation] = {}
        self.case_notes: Dict[str, List[CaseNote]] = {}
        self.expert_availability: Dict[str, List[ExpertAvailability]] = {}
        
        # Initialize with demo experts
        self._create_demo_experts()
        
        logger.info("👨‍💼 Expert Dashboard Manager initialized")
    
    def _create_demo_experts(self):
        """Create demo expert profiles"""
        
        # GDPR Expert
        gdpr_expert = Expert(
            expert_id=str(uuid.uuid4()),
            email="dr.mueller@complyo.tech",
            first_name="Dr. Sarah",
            last_name="Müller",
            title="Rechtsanwältin für Datenschutzrecht",
            specialties=[ExpertSpecialty.GDPR_COMPLIANCE, ExpertSpecialty.PRIVACY_LAW],
            languages=["de", "en"],
            hourly_rate=250.0,
            bio="Spezialistin für DSGVO-Compliance mit über 10 Jahren Erfahrung im Datenschutzrecht.",
            certifications=["Certified Data Protection Officer", "IAPP CIPP/E"],
            years_experience=12,
            rating=4.9,
            total_consultations=156
        )
        
        # Website Law Expert
        website_expert = Expert(
            expert_id=str(uuid.uuid4()),
            email="ra.schmidt@complyo.tech", 
            first_name="RA Marcus",
            last_name="Schmidt",
            title="Fachanwalt für IT-Recht",
            specialties=[ExpertSpecialty.WEBSITE_LAW, ExpertSpecialty.ECOMMERCE_LAW],
            languages=["de", "en"],
            hourly_rate=220.0,
            bio="Fachanwalt für IT-Recht mit Fokus auf Website-Compliance und E-Commerce.",
            certifications=["Fachanwalt IT-Recht", "Certified IT-Security Expert"],
            years_experience=8,
            rating=4.8,
            total_consultations=89
        )
        
        # Technical Expert
        tech_expert = Expert(
            expert_id=str(uuid.uuid4()),
            email="tech.weber@complyo.tech",
            first_name="Lisa",
            last_name="Weber",
            title="Technical Compliance Specialist",
            specialties=[ExpertSpecialty.TECHNICAL_COMPLIANCE, ExpertSpecialty.ACCESSIBILITY],
            languages=["de", "en"],
            hourly_rate=180.0,
            bio="Technische Expertin für Website-Accessibility und technische DSGVO-Umsetzung.",
            certifications=["WCAG 2.1 Certified", "BITV 2.0 Specialist"],
            years_experience=6,
            rating=4.9,
            total_consultations=73
        )
        
        # Store experts
        for expert in [gdpr_expert, website_expert, tech_expert]:
            self.experts[expert.expert_id] = expert
            self.expert_availability[expert.expert_id] = []
            
            # Generate availability for next 4 weeks
            self._generate_expert_availability(expert.expert_id)
        
        logger.info(f"👥 Created {len(self.experts)} demo experts")
    
    def _generate_expert_availability(self, expert_id: str):
        """Generate availability slots for expert"""
        
        expert = self.experts.get(expert_id)
        if not expert:
            return
        
        # Generate slots for next 4 weeks
        start_date = datetime.now().date()
        
        for day_offset in range(28):
            date = start_date + timedelta(days=day_offset)
            weekday = date.strftime("%A").lower()
            
            if weekday in expert.availability_schedule:
                schedule = expert.availability_schedule[weekday]
                if schedule:  # Check if expert works this day
                    start_time, end_time = schedule
                    
                    # Create availability slots (2-hour blocks)
                    current_time = datetime.strptime(start_time, "%H:%M").time()
                    end_time_obj = datetime.strptime(end_time, "%H:%M").time()
                    
                    while current_time < end_time_obj:
                        next_time = (datetime.combine(date, current_time) + timedelta(hours=2)).time()
                        if next_time <= end_time_obj:
                            availability = ExpertAvailability(
                                expert_id=expert_id,
                                date=datetime.combine(date, current_time),
                                start_time=current_time.strftime("%H:%M"),
                                end_time=next_time.strftime("%H:%M")
                            )
                            self.expert_availability[expert_id].append(availability)
                        
                        current_time = next_time
    
    async def create_consultation_request(self, request_data: Dict[str, Any]) -> str:
        """Create new consultation request"""
        
        try:
            request_id = str(uuid.uuid4())
            
            request = ConsultationRequest(
                request_id=request_id,
                client_id=request_data["client_id"],
                consultation_type=ConsultationType(request_data["consultation_type"]),
                title=request_data["title"],
                description=request_data["description"],
                priority=Priority(request_data.get("priority", "medium")),
                website_urls=request_data.get("website_urls", []),
                preferred_language=request_data.get("preferred_language", "de"),
                preferred_datetime=request_data.get("preferred_datetime"),
                budget_range=request_data.get("budget_range"),
                urgency_reason=request_data.get("urgency_reason"),
                attachments=request_data.get("attachments", [])
            )
            
            self.consultation_requests[request_id] = request
            
            # Auto-assign expert if available
            expert_id = await self._auto_assign_expert(request)
            if expert_id:
                consultation_id = await self._create_consultation_from_request(request, expert_id)
                logger.info(f"💼 Auto-assigned consultation {consultation_id} to expert {expert_id}")
            
            logger.info(f"📝 Consultation request created: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Request creation failed: {str(e)}")
            raise
    
    async def _auto_assign_expert(self, request: ConsultationRequest) -> Optional[str]:
        """Automatically assign best matching expert"""
        
        try:
            # Find experts with matching specialties
            matching_experts = []
            
            for expert_id, expert in self.experts.items():
                if not expert.is_available:
                    continue
                
                # Check specialty match
                specialty_match = False
                if request.consultation_type == ConsultationType.COMPLIANCE_REVIEW:
                    specialty_match = ExpertSpecialty.GDPR_COMPLIANCE in expert.specialties
                elif request.consultation_type == ConsultationType.LEGAL_ADVICE:
                    specialty_match = ExpertSpecialty.PRIVACY_LAW in expert.specialties or ExpertSpecialty.WEBSITE_LAW in expert.specialties
                elif request.consultation_type == ConsultationType.TECHNICAL_SUPPORT:
                    specialty_match = ExpertSpecialty.TECHNICAL_COMPLIANCE in expert.specialties
                else:
                    specialty_match = True  # General consultation
                
                if specialty_match and request.preferred_language in expert.languages:
                    matching_experts.append((expert_id, expert))
            
            if not matching_experts:
                return None
            
            # Select best expert (highest rating, then lowest workload)
            best_expert = max(matching_experts, key=lambda x: (x[1].rating, -x[1].total_consultations))
            return best_expert[0]
            
        except Exception as e:
            logger.error(f"Auto-assignment failed: {str(e)}")
            return None
    
    async def _create_consultation_from_request(self, request: ConsultationRequest, expert_id: str) -> str:
        """Create consultation from request"""
        
        consultation_id = str(uuid.uuid4())
        
        consultation = Consultation(
            consultation_id=consultation_id,
            client_id=request.client_id,
            expert_id=expert_id,
            request=request,
            status=ConsultationStatus.ASSIGNED
        )
        
        self.consultations[consultation_id] = consultation
        self.case_notes[consultation_id] = []
        
        # Add initial case note
        initial_note = CaseNote(
            note_id=str(uuid.uuid4()),
            consultation_id=consultation_id,
            author_id="system",
            author_type="admin",
            content=f"Consultation assigned to expert {expert_id}. Client request: {request.title}",
            note_type="progress"
        )
        
        self.case_notes[consultation_id].append(initial_note)
        
        return consultation_id
    
    async def schedule_consultation(self, consultation_id: str, schedule_data: Dict[str, Any]) -> bool:
        """Schedule consultation appointment"""
        
        try:
            consultation = self.consultations.get(consultation_id)
            if not consultation:
                return False
            
            # Update consultation
            consultation.scheduled_datetime = schedule_data["datetime"]
            consultation.duration_minutes = schedule_data.get("duration_minutes", 60)
            consultation.meeting_link = schedule_data.get("meeting_link")
            consultation.meeting_password = schedule_data.get("meeting_password")
            consultation.status = ConsultationStatus.SCHEDULED
            consultation.updated_at = datetime.now()
            
            # Block expert availability
            expert_id = consultation.expert_id
            if expert_id and expert_id in self.expert_availability:
                for availability in self.expert_availability[expert_id]:
                    if (availability.date.date() == consultation.scheduled_datetime.date() and
                        availability.start_time <= consultation.scheduled_datetime.strftime("%H:%M") < availability.end_time):
                        availability.is_available = False
                        availability.consultation_id = consultation_id
                        break
            
            # Add scheduling note
            schedule_note = CaseNote(
                note_id=str(uuid.uuid4()),
                consultation_id=consultation_id,
                author_id=expert_id or "admin",
                author_type="expert" if expert_id else "admin",
                content=f"Consultation scheduled for {consultation.scheduled_datetime.strftime('%d.%m.%Y %H:%M')}",
                note_type="progress"
            )
            
            self.case_notes[consultation_id].append(schedule_note)
            
            logger.info(f"📅 Consultation {consultation_id} scheduled")
            return True
            
        except Exception as e:
            logger.error(f"Scheduling failed: {str(e)}")
            return False
    
    async def start_consultation(self, consultation_id: str, expert_id: str) -> bool:
        """Start consultation session"""
        
        try:
            consultation = self.consultations.get(consultation_id)
            if not consultation or consultation.expert_id != expert_id:
                return False
            
            consultation.status = ConsultationStatus.IN_PROGRESS
            consultation.updated_at = datetime.now()
            
            # Add start note
            start_note = CaseNote(
                note_id=str(uuid.uuid4()),
                consultation_id=consultation_id,
                author_id=expert_id,
                author_type="expert",
                content="Consultation session started",
                note_type="progress"
            )
            
            self.case_notes[consultation_id].append(start_note)
            
            logger.info(f"▶️ Consultation {consultation_id} started")
            return True
            
        except Exception as e:
            logger.error(f"Start consultation failed: {str(e)}")
            return False
    
    async def complete_consultation(self, consultation_id: str, completion_data: Dict[str, Any]) -> bool:
        """Complete consultation with summary and recommendations"""
        
        try:
            consultation = self.consultations.get(consultation_id)
            if not consultation:
                return False
            
            # Update consultation
            consultation.status = ConsultationStatus.COMPLETED
            consultation.completion_summary = completion_data.get("summary")
            consultation.expert_recommendations = completion_data.get("recommendations", [])
            consultation.total_cost = completion_data.get("total_cost", 0.0)
            consultation.completed_at = datetime.now()
            consultation.updated_at = datetime.now()
            
            # Check if follow-up required
            if completion_data.get("follow_up_required"):
                consultation.status = ConsultationStatus.FOLLOW_UP_REQUIRED
                consultation.follow_up_date = completion_data.get("follow_up_date")
                consultation.follow_up_tasks = completion_data.get("follow_up_tasks", [])
            
            # Add completion note
            completion_note = CaseNote(
                note_id=str(uuid.uuid4()),
                consultation_id=consultation_id,
                author_id=consultation.expert_id or "system",
                author_type="expert",
                content=f"Consultation completed. Summary: {consultation.completion_summary[:100]}...",
                note_type="progress"
            )
            
            self.case_notes[consultation_id].append(completion_note)
            
            # Update expert stats
            expert = self.experts.get(consultation.expert_id)
            if expert:
                expert.total_consultations += 1
            
            logger.info(f"✅ Consultation {consultation_id} completed")
            return True
            
        except Exception as e:
            logger.error(f"Complete consultation failed: {str(e)}")
            return False
    
    async def add_case_note(self, consultation_id: str, note_data: Dict[str, Any]) -> str:
        """Add note to consultation case"""
        
        try:
            note_id = str(uuid.uuid4())
            
            note = CaseNote(
                note_id=note_id,
                consultation_id=consultation_id,
                author_id=note_data["author_id"],
                author_type=note_data["author_type"],
                content=note_data["content"],
                note_type=note_data.get("note_type", "progress"),
                is_private=note_data.get("is_private", False)
            )
            
            if consultation_id not in self.case_notes:
                self.case_notes[consultation_id] = []
            
            self.case_notes[consultation_id].append(note)
            
            # Update consultation timestamp
            consultation = self.consultations.get(consultation_id)
            if consultation:
                consultation.updated_at = datetime.now()
            
            logger.info(f"📝 Case note added: {note_id}")
            return note_id
            
        except Exception as e:
            logger.error(f"Add note failed: {str(e)}")
            raise
    
    async def rate_consultation(self, consultation_id: str, client_id: str, rating_data: Dict[str, Any]) -> bool:
        """Client rates completed consultation"""
        
        try:
            consultation = self.consultations.get(consultation_id)
            if not consultation or consultation.client_id != client_id:
                return False
            
            consultation.client_rating = rating_data["rating"]
            consultation.client_feedback = rating_data.get("feedback")
            consultation.updated_at = datetime.now()
            
            # Update expert rating
            expert = self.experts.get(consultation.expert_id)
            if expert and expert.total_consultations > 0:
                # Simple average - in production use more sophisticated algorithm
                expert.rating = (expert.rating * (expert.total_consultations - 1) + rating_data["rating"]) / expert.total_consultations
            
            # Add rating note
            rating_note = CaseNote(
                note_id=str(uuid.uuid4()),
                consultation_id=consultation_id,
                author_id=client_id,
                author_type="client",
                content=f"Client rating: {rating_data['rating']}/5. Feedback: {rating_data.get('feedback', 'No feedback')}",
                note_type="progress"
            )
            
            self.case_notes[consultation_id].append(rating_note)
            
            logger.info(f"⭐ Consultation {consultation_id} rated: {rating_data['rating']}/5")
            return True
            
        except Exception as e:
            logger.error(f"Rating failed: {str(e)}")
            return False
    
    # ========== EXPERT DASHBOARD QUERIES ==========
    
    async def get_expert_dashboard(self, expert_id: str) -> Dict[str, Any]:
        """Get expert dashboard overview"""
        
        try:
            expert = self.experts.get(expert_id)
            if not expert:
                return {}
            
            # Get expert's consultations
            expert_consultations = [
                consultation for consultation in self.consultations.values()
                if consultation.expert_id == expert_id
            ]
            
            # Calculate metrics
            total_consultations = len(expert_consultations)
            completed_consultations = len([c for c in expert_consultations if c.status == ConsultationStatus.COMPLETED])
            pending_consultations = len([c for c in expert_consultations if c.status in [ConsultationStatus.ASSIGNED, ConsultationStatus.SCHEDULED]])
            in_progress_consultations = len([c for c in expert_consultations if c.status == ConsultationStatus.IN_PROGRESS])
            
            # Revenue calculation
            total_revenue = sum([c.total_cost for c in expert_consultations if c.total_cost])
            
            # Upcoming appointments
            upcoming = [
                c for c in expert_consultations
                if c.scheduled_datetime and c.scheduled_datetime > datetime.now() and c.status == ConsultationStatus.SCHEDULED
            ]
            upcoming.sort(key=lambda x: x.scheduled_datetime)
            
            # Recent activity
            recent_notes = []
            for consultation in expert_consultations[-10:]:  # Last 10 consultations
                if consultation.consultation_id in self.case_notes:
                    recent_notes.extend(self.case_notes[consultation.consultation_id][-3:])  # Last 3 notes per case
            
            recent_notes.sort(key=lambda x: x.created_at, reverse=True)
            
            return {
                "expert": asdict(expert),
                "metrics": {
                    "total_consultations": total_consultations,
                    "completed_consultations": completed_consultations,
                    "pending_consultations": pending_consultations,
                    "in_progress_consultations": in_progress_consultations,
                    "total_revenue": total_revenue,
                    "average_rating": expert.rating,
                    "completion_rate": (completed_consultations / total_consultations * 100) if total_consultations > 0 else 0
                },
                "upcoming_appointments": [
                    {
                        "consultation_id": c.consultation_id,
                        "client_name": f"Client {c.client_id[:8]}",  # In production: get real client name
                        "title": c.request.title,
                        "scheduled_datetime": c.scheduled_datetime.isoformat(),
                        "duration_minutes": c.duration_minutes,
                        "meeting_link": c.meeting_link
                    }
                    for c in upcoming[:5]  # Next 5 appointments
                ],
                "recent_activity": [
                    {
                        "note_id": note.note_id,
                        "consultation_id": note.consultation_id,
                        "content": note.content[:100] + "..." if len(note.content) > 100 else note.content,
                        "note_type": note.note_type,
                        "created_at": note.created_at.isoformat()
                    }
                    for note in recent_notes[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Expert dashboard failed: {str(e)}")
            return {}
    
    async def get_expert_consultations(self, expert_id: str, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get consultations for expert"""
        
        try:
            expert_consultations = [
                consultation for consultation in self.consultations.values()
                if consultation.expert_id == expert_id
            ]
            
            # Filter by status if specified
            if status:
                expert_consultations = [c for c in expert_consultations if c.status.value == status]
            
            # Sort by updated_at descending
            expert_consultations.sort(key=lambda x: x.updated_at, reverse=True)
            
            # Limit results
            expert_consultations = expert_consultations[:limit]
            
            # Convert to dict format
            result = []
            for consultation in expert_consultations:
                notes_count = len(self.case_notes.get(consultation.consultation_id, []))
                
                result.append({
                    "consultation_id": consultation.consultation_id,
                    "client_id": consultation.client_id,
                    "request": asdict(consultation.request),
                    "status": consultation.status.value,
                    "scheduled_datetime": consultation.scheduled_datetime.isoformat() if consultation.scheduled_datetime else None,
                    "duration_minutes": consultation.duration_minutes,
                    "total_cost": consultation.total_cost,
                    "notes_count": notes_count,
                    "client_rating": consultation.client_rating,
                    "created_at": consultation.created_at.isoformat(),
                    "updated_at": consultation.updated_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Get consultations failed: {str(e)}")
            return []
    
    async def get_consultation_details(self, consultation_id: str, user_id: str, user_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed consultation information"""
        
        try:
            consultation = self.consultations.get(consultation_id)
            if not consultation:
                return None
            
            # Check access permissions
            if user_type == "expert" and consultation.expert_id != user_id:
                return None
            elif user_type == "client" and consultation.client_id != user_id:
                return None
            
            # Get case notes (filter private notes if not expert)
            case_notes = self.case_notes.get(consultation_id, [])
            if user_type != "expert":
                case_notes = [note for note in case_notes if not note.is_private]
            
            # Get expert info
            expert_info = None
            if consultation.expert_id:
                expert = self.experts.get(consultation.expert_id)
                if expert:
                    expert_info = {
                        "name": f"{expert.first_name} {expert.last_name}",
                        "title": expert.title,
                        "specialties": [s.value for s in expert.specialties],
                        "rating": expert.rating,
                        "bio": expert.bio
                    }
            
            return {
                "consultation": asdict(consultation),
                "expert_info": expert_info,
                "case_notes": [asdict(note) for note in case_notes],
                "total_notes": len(case_notes)
            }
            
        except Exception as e:
            logger.error(f"Get consultation details failed: {str(e)}")
            return None
    
    async def get_available_experts(self, consultation_type: str = None, language: str = "de") -> List[Dict[str, Any]]:
        """Get list of available experts"""
        
        try:
            available_experts = [
                expert for expert in self.experts.values()
                if expert.is_available and language in expert.languages
            ]
            
            # Filter by consultation type if specified
            if consultation_type:
                type_enum = ConsultationType(consultation_type)
                filtered_experts = []
                
                for expert in available_experts:
                    if type_enum == ConsultationType.COMPLIANCE_REVIEW and ExpertSpecialty.GDPR_COMPLIANCE in expert.specialties:
                        filtered_experts.append(expert)
                    elif type_enum == ConsultationType.LEGAL_ADVICE and (ExpertSpecialty.PRIVACY_LAW in expert.specialties or ExpertSpecialty.WEBSITE_LAW in expert.specialties):
                        filtered_experts.append(expert)
                    elif type_enum == ConsultationType.TECHNICAL_SUPPORT and ExpertSpecialty.TECHNICAL_COMPLIANCE in expert.specialties:
                        filtered_experts.append(expert)
                    else:
                        filtered_experts.append(expert)  # General consultation
                
                available_experts = filtered_experts
            
            # Sort by rating
            available_experts.sort(key=lambda x: x.rating, reverse=True)
            
            # Convert to response format
            result = []
            for expert in available_experts:
                result.append({
                    "expert_id": expert.expert_id,
                    "name": f"{expert.first_name} {expert.last_name}",
                    "title": expert.title,
                    "specialties": [s.value for s in expert.specialties],
                    "languages": expert.languages,
                    "hourly_rate": expert.hourly_rate,
                    "rating": expert.rating,
                    "total_consultations": expert.total_consultations,
                    "bio": expert.bio,
                    "certifications": expert.certifications
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Get available experts failed: {str(e)}")
            return []
    
    async def get_expert_availability(self, expert_id: str, days: int = 14) -> List[Dict[str, Any]]:
        """Get expert availability for next N days"""
        
        try:
            if expert_id not in self.expert_availability:
                return []
            
            cutoff_date = datetime.now() + timedelta(days=days)
            
            available_slots = [
                availability for availability in self.expert_availability[expert_id]
                if availability.is_available and availability.date <= cutoff_date and availability.date >= datetime.now()
            ]
            
            # Sort by date/time
            available_slots.sort(key=lambda x: x.date)
            
            return [
                {
                    "date": slot.date.strftime("%Y-%m-%d"),
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "datetime": slot.date.strftime("%Y-%m-%d %H:%M")
                }
                for slot in available_slots
            ]
            
        except Exception as e:
            logger.error(f"Get availability failed: {str(e)}")
            return []
    
    # ========== ADMIN FUNCTIONS ==========
    
    async def get_admin_dashboard(self) -> Dict[str, Any]:
        """Get admin dashboard with system overview"""
        
        try:
            total_experts = len(self.experts)
            available_experts = len([e for e in self.experts.values() if e.is_available])
            
            total_consultations = len(self.consultations)
            pending_requests = len(self.consultation_requests)
            
            # Status breakdown
            status_counts = {}
            for status in ConsultationStatus:
                status_counts[status.value] = len([c for c in self.consultations.values() if c.status == status])
            
            # Revenue metrics
            total_revenue = sum([c.total_cost for c in self.consultations.values() if c.total_cost])
            avg_consultation_value = total_revenue / total_consultations if total_consultations > 0 else 0
            
            # Recent activity
            recent_consultations = sorted(self.consultations.values(), key=lambda x: x.updated_at, reverse=True)[:10]
            
            return {
                "overview": {
                    "total_experts": total_experts,
                    "available_experts": available_experts,
                    "total_consultations": total_consultations,
                    "pending_requests": pending_requests,
                    "total_revenue": total_revenue,
                    "avg_consultation_value": avg_consultation_value
                },
                "status_breakdown": status_counts,
                "recent_activity": [
                    {
                        "consultation_id": c.consultation_id,
                        "client_id": c.client_id,
                        "expert_id": c.expert_id,
                        "status": c.status.value,
                        "title": c.request.title,
                        "updated_at": c.updated_at.isoformat()
                    }
                    for c in recent_consultations
                ]
            }
            
        except Exception as e:
            logger.error(f"Admin dashboard failed: {str(e)}")
            return {}
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        
        try:
            # Time-based metrics (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            
            recent_consultations = [
                c for c in self.consultations.values()
                if c.created_at >= cutoff_date
            ]
            
            # Performance metrics
            avg_completion_time = 0
            completed_recent = [c for c in recent_consultations if c.completed_at]
            if completed_recent:
                completion_times = [
                    (c.completed_at - c.created_at).total_seconds() / 3600  # Hours
                    for c in completed_recent
                ]
                avg_completion_time = sum(completion_times) / len(completion_times)
            
            # Expert performance
            expert_stats = {}
            for expert_id, expert in self.experts.items():
                expert_consultations = [c for c in self.consultations.values() if c.expert_id == expert_id]
                expert_stats[expert_id] = {
                    "name": f"{expert.first_name} {expert.last_name}",
                    "total_consultations": len(expert_consultations),
                    "completed_consultations": len([c for c in expert_consultations if c.status == ConsultationStatus.COMPLETED]),
                    "average_rating": expert.rating,
                    "total_revenue": sum([c.total_cost for c in expert_consultations if c.total_cost])
                }
            
            return {
                "period_stats": {
                    "period_days": 30,
                    "total_consultations": len(recent_consultations),
                    "completed_consultations": len(completed_recent),
                    "avg_completion_time_hours": avg_completion_time,
                    "total_revenue": sum([c.total_cost for c in recent_consultations if c.total_cost])
                },
                "expert_performance": expert_stats,
                "consultation_types": {
                    consultation_type.value: len([
                        c for c in recent_consultations
                        if c.request.consultation_type == consultation_type
                    ])
                    for consultation_type in ConsultationType
                }
            }
            
        except Exception as e:
            logger.error(f"System statistics failed: {str(e)}")
            return {}

# Global expert dashboard instance
expert_dashboard = ExpertDashboardManager()