"""
Media Accessibility Check (WCAG 1.2.x)
Prüft Video- und Audio-Elemente auf Barrierefreiheit

WCAG Kriterien:
- 1.2.1: Audio-only and Video-only (Prerecorded)
- 1.2.2: Captions (Prerecorded)
- 1.2.3: Audio Description or Media Alternative (Prerecorded)
- 1.2.4: Captions (Live) - Level AA
- 1.2.5: Audio Description (Prerecorded) - Level AA
"""

from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
import re
from urllib.parse import urljoin, urlparse
import logging
import aiohttp

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class MediaElement:
    """Ein Media-Element (Video/Audio/Iframe)"""
    type: str  # video, audio, iframe
    src: str
    has_captions: bool = False
    has_audio_description: bool = False
    has_transcript: bool = False
    has_controls: bool = True
    autoplay: bool = False
    muted: bool = False
    
    # Track-Informationen
    caption_tracks: List[str] = field(default_factory=list)
    description_tracks: List[str] = field(default_factory=list)
    
    # Kontext
    parent_context: str = ""
    surrounding_text: str = ""
    
    # Embed-Typ
    embed_provider: Optional[str] = None  # youtube, vimeo, etc.


@dataclass
class MediaAccessibilityIssue:
    """Ein Media-Barrierefreiheits-Problem"""
    category: str = "media_accessibility"
    severity: str = "error"
    title: str = ""
    description: str = ""
    wcag_criteria: List[str] = field(default_factory=list)
    legal_basis: str = ""
    recommendation: str = ""
    risk_euro: int = 1500
    auto_fixable: bool = False
    
    # Media-spezifisch
    media_type: str = ""
    media_src: str = ""
    element_html: str = ""
    page_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Media Patterns
# =============================================================================

# Bekannte Video-Embed-Patterns
EMBED_PATTERNS = {
    "youtube": [
        r'youtube\.com/embed/',
        r'youtube\.com/watch',
        r'youtu\.be/',
        r'youtube-nocookie\.com'
    ],
    "vimeo": [
        r'vimeo\.com/',
        r'player\.vimeo\.com/'
    ],
    "dailymotion": [
        r'dailymotion\.com/'
    ],
    "wistia": [
        r'wistia\.com/',
        r'wi\.st/'
    ],
    "twitch": [
        r'twitch\.tv/'
    ]
}


# =============================================================================
# Media Accessibility Checker
# =============================================================================

class MediaAccessibilityChecker:
    """
    Prüft Media-Elemente auf WCAG 1.2.x Compliance
    """
    
    def __init__(self):
        logger.info("🔧 MediaAccessibilityChecker initialisiert")
    
    async def check_page(
        self,
        url: str,
        soup: BeautifulSoup
    ) -> List[MediaAccessibilityIssue]:
        """
        Prüft alle Media-Elemente einer Seite
        
        Args:
            url: URL der Seite
            soup: BeautifulSoup-Objekt
            
        Returns:
            Liste von Issues
        """
        logger.info(f"🎬 Media-Check: {url}")
        
        issues = []
        
        # 1. Video-Elemente prüfen
        video_issues = self._check_video_elements(url, soup)
        issues.extend(video_issues)
        
        # 2. Audio-Elemente prüfen
        audio_issues = self._check_audio_elements(url, soup)
        issues.extend(audio_issues)
        
        # 3. Iframe-Embeds prüfen (YouTube, Vimeo, etc.)
        iframe_issues = self._check_iframe_embeds(url, soup)
        issues.extend(iframe_issues)
        
        # 4. Autoplay ohne Mute prüfen (WCAG 1.4.2)
        autoplay_issues = self._check_autoplay(url, soup)
        issues.extend(autoplay_issues)
        
        logger.info(f"✅ Media-Check abgeschlossen: {len(issues)} Issues")
        return issues
    
    def _check_video_elements(
        self,
        url: str,
        soup: BeautifulSoup
    ) -> List[MediaAccessibilityIssue]:
        """Prüft <video> Elemente"""
        issues = []
        
        videos = soup.find_all('video')
        
        for video in videos:
            media = self._parse_video_element(video, url)
            
            # Prüfe Untertitel (WCAG 1.2.2)
            if not media.has_captions:
                issues.append(MediaAccessibilityIssue(
                    title="Video ohne Untertitel",
                    description=f"Das Video hat keine Untertitel (<track kind='captions'>). "
                               f"Gehörlose und schwerhörige Nutzer können den Audioinhalt nicht verstehen.",
                    severity="critical",
                    wcag_criteria=["1.2.2", "1.2.4"],
                    legal_basis="WCAG 2.1 Level A (1.2.2), BFSG §12",
                    recommendation="Fügen Sie Untertitel hinzu: <track kind='captions' src='untertitel.vtt' srclang='de' label='Deutsch'>",
                    media_type="video",
                    media_src=media.src,
                    element_html=str(video)[:300],
                    page_url=url,
                    risk_euro=2000
                ))
            
            # Prüfe Audiodeskription (WCAG 1.2.5)
            if not media.has_audio_description:
                issues.append(MediaAccessibilityIssue(
                    title="Video ohne Audiodeskription",
                    description="Das Video hat keine Audiodeskription für blinde Nutzer. "
                               "Visuelle Informationen, die nicht durch den Ton vermittelt werden, "
                               "sind nicht zugänglich.",
                    severity="warning",
                    wcag_criteria=["1.2.3", "1.2.5"],
                    legal_basis="WCAG 2.1 Level AA (1.2.5), BFSG §12",
                    recommendation="Fügen Sie eine Audiodeskription hinzu oder stellen Sie eine Textalternative bereit.",
                    media_type="video",
                    media_src=media.src,
                    element_html=str(video)[:300],
                    page_url=url,
                    risk_euro=1500
                ))
            
            # Prüfe Transkript-Verlinkung
            if not media.has_transcript:
                # Suche nach Transkript-Links in der Nähe
                has_nearby_transcript = self._has_nearby_transcript(video, soup)
                if not has_nearby_transcript:
                    issues.append(MediaAccessibilityIssue(
                        title="Video ohne Transkript-Link",
                        description="Es wurde kein Transkript für das Video gefunden. "
                                   "Transkripte helfen Nutzern, die das Video nicht ansehen können oder wollen.",
                        severity="info",
                        wcag_criteria=["1.2.1", "1.2.3"],
                        legal_basis="WCAG 2.1 Level A (1.2.1), Best Practice",
                        recommendation="Stellen Sie ein vollständiges Transkript bereit und verlinken Sie es unter dem Video.",
                        media_type="video",
                        media_src=media.src,
                        element_html=str(video)[:300],
                        page_url=url,
                        risk_euro=800
                    ))
        
        return issues
    
    def _check_audio_elements(
        self,
        url: str,
        soup: BeautifulSoup
    ) -> List[MediaAccessibilityIssue]:
        """Prüft <audio> Elemente"""
        issues = []
        
        audios = soup.find_all('audio')
        
        for audio in audios:
            media = self._parse_audio_element(audio, url)
            
            # Prüfe Transkript (WCAG 1.2.1)
            has_nearby_transcript = self._has_nearby_transcript(audio, soup)
            
            if not has_nearby_transcript:
                issues.append(MediaAccessibilityIssue(
                    title="Audio ohne Transkript",
                    description="Der Audioinhalt hat kein Transkript. "
                               "Gehörlose Nutzer können den Inhalt nicht verstehen.",
                    severity="error",
                    wcag_criteria=["1.2.1"],
                    legal_basis="WCAG 2.1 Level A (1.2.1), BFSG §12",
                    recommendation="Stellen Sie ein vollständiges Transkript bereit und verlinken Sie es beim Audio-Player.",
                    media_type="audio",
                    media_src=media.src,
                    element_html=str(audio)[:300],
                    page_url=url,
                    risk_euro=1500
                ))
        
        return issues
    
    def _check_iframe_embeds(
        self,
        url: str,
        soup: BeautifulSoup
    ) -> List[MediaAccessibilityIssue]:
        """Prüft <iframe> Video-Embeds"""
        issues = []
        
        iframes = soup.find_all('iframe')
        
        for iframe in iframes:
            src = iframe.get('src', '')
            
            # Ermittle Embed-Provider
            provider = self._detect_embed_provider(src)
            
            if provider:
                # Es ist ein Video-Embed
                title = iframe.get('title', '')
                
                # Prüfe auf fehlenden Titel (WCAG 4.1.2)
                if not title:
                    issues.append(MediaAccessibilityIssue(
                        title=f"{provider.capitalize()}-Video ohne Titel",
                        description=f"Das eingebettete {provider.capitalize()}-Video hat keinen title-Attribut. "
                                   f"Screenreader können das Video nicht identifizieren.",
                        severity="warning",
                        wcag_criteria=["4.1.2"],
                        legal_basis="WCAG 2.1 Level A (4.1.2), BFSG §12",
                        recommendation=f"Fügen Sie ein title-Attribut hinzu: <iframe title='Beschreibung des Videos' ...>",
                        media_type="iframe",
                        media_src=src,
                        element_html=str(iframe)[:300],
                        page_url=url,
                        risk_euro=500
                    ))
                
                # Hinweis auf externe Untertitel
                issues.append(MediaAccessibilityIssue(
                    title=f"{provider.capitalize()}-Video: Untertitel prüfen",
                    description=f"Stellen Sie sicher, dass das eingebettete {provider.capitalize()}-Video "
                               f"Untertitel aktiviert hat. Bei externen Embeds muss dies auf der Plattform konfiguriert werden.",
                    severity="info",
                    wcag_criteria=["1.2.2"],
                    legal_basis="WCAG 2.1 Level A (1.2.2), Best Practice",
                    recommendation=f"Aktivieren Sie Untertitel in den {provider.capitalize()}-Einstellungen "
                                  f"oder nutzen Sie die cc=1 oder captions Parameter in der URL.",
                    media_type="iframe",
                    media_src=src,
                    element_html=str(iframe)[:300],
                    page_url=url,
                    risk_euro=0,
                    auto_fixable=False
                ))
        
        return issues
    
    def _check_autoplay(
        self,
        url: str,
        soup: BeautifulSoup
    ) -> List[MediaAccessibilityIssue]:
        """Prüft auf problematisches Autoplay (WCAG 1.4.2)"""
        issues = []
        
        # Videos mit Autoplay
        autoplay_videos = soup.find_all('video', autoplay=True)
        autoplay_videos.extend(soup.find_all('video', attrs={'autoplay': ''}))
        
        for video in autoplay_videos:
            muted = video.has_attr('muted') or video.get('muted') == ''
            
            if not muted:
                issues.append(MediaAccessibilityIssue(
                    title="Video mit Autoplay ohne Stummschaltung",
                    description="Das Video startet automatisch mit Ton. "
                               "Dies kann Screenreader-Nutzer stören und ist unerwartet für alle Nutzer.",
                    severity="error",
                    wcag_criteria=["1.4.2"],
                    legal_basis="WCAG 2.1 Level A (1.4.2), BFSG §12",
                    recommendation="Entfernen Sie autoplay oder fügen Sie muted hinzu: <video autoplay muted>",
                    media_type="video",
                    media_src=video.get('src', ''),
                    element_html=str(video)[:300],
                    page_url=url,
                    risk_euro=1000
                ))
        
        # Audios mit Autoplay
        autoplay_audios = soup.find_all('audio', autoplay=True)
        autoplay_audios.extend(soup.find_all('audio', attrs={'autoplay': ''}))
        
        for audio in autoplay_audios:
            issues.append(MediaAccessibilityIssue(
                title="Audio mit Autoplay",
                description="Der Audio-Player startet automatisch. "
                           "Dies stört Screenreader-Nutzer und ist unerwartet.",
                severity="critical",
                wcag_criteria=["1.4.2"],
                legal_basis="WCAG 2.1 Level A (1.4.2), BFSG §12",
                recommendation="Entfernen Sie das autoplay-Attribut: <audio controls> statt <audio autoplay controls>",
                media_type="audio",
                media_src=audio.get('src', ''),
                element_html=str(audio)[:300],
                page_url=url,
                risk_euro=1500
            ))
        
        return issues
    
    def _parse_video_element(self, video: Tag, base_url: str) -> MediaElement:
        """Parst ein <video> Element"""
        src = video.get('src', '')
        
        # Auch <source> Elemente prüfen
        if not src:
            source = video.find('source')
            if source:
                src = source.get('src', '')
        
        # Absolute URL
        if src and not src.startswith(('http://', 'https://', 'data:')):
            src = urljoin(base_url, src)
        
        # Track-Elemente prüfen
        tracks = video.find_all('track')
        caption_tracks = []
        description_tracks = []
        
        for track in tracks:
            kind = track.get('kind', '').lower()
            track_src = track.get('src', '')
            
            if kind in ['captions', 'subtitles']:
                caption_tracks.append(track_src)
            elif kind == 'descriptions':
                description_tracks.append(track_src)
        
        return MediaElement(
            type="video",
            src=src,
            has_captions=len(caption_tracks) > 0,
            has_audio_description=len(description_tracks) > 0,
            has_controls=video.has_attr('controls'),
            autoplay=video.has_attr('autoplay'),
            muted=video.has_attr('muted'),
            caption_tracks=caption_tracks,
            description_tracks=description_tracks
        )
    
    def _parse_audio_element(self, audio: Tag, base_url: str) -> MediaElement:
        """Parst ein <audio> Element"""
        src = audio.get('src', '')
        
        if not src:
            source = audio.find('source')
            if source:
                src = source.get('src', '')
        
        if src and not src.startswith(('http://', 'https://', 'data:')):
            src = urljoin(base_url, src)
        
        return MediaElement(
            type="audio",
            src=src,
            has_controls=audio.has_attr('controls'),
            autoplay=audio.has_attr('autoplay')
        )
    
    def _detect_embed_provider(self, src: str) -> Optional[str]:
        """Ermittelt den Embed-Provider"""
        if not src:
            return None
        
        for provider, patterns in EMBED_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, src, re.I):
                    return provider
        
        return None
    
    def _has_nearby_transcript(self, element: Tag, soup: BeautifulSoup) -> bool:
        """
        Sucht nach Transkript-Links in der Nähe des Elements
        """
        # Suche im Parent
        parent = element.parent
        if parent:
            # Suche nach Links mit Transkript-Keywords
            links = parent.find_all('a', href=True)
            for link in links:
                text = link.get_text(strip=True).lower()
                href = link.get('href', '').lower()
                
                if any(kw in text or kw in href for kw in 
                       ['transkript', 'transcript', 'text', 'skript', 'niederschrift']):
                    return True
        
        # Suche nach aria-describedby
        described_by = element.get('aria-describedby')
        if described_by:
            desc_element = soup.find(id=described_by)
            if desc_element and len(desc_element.get_text(strip=True)) > 50:
                return True
        
        return False


# Globale Instanz
media_checker = MediaAccessibilityChecker()


# =============================================================================
# Convenience Function
# =============================================================================

async def check_media_accessibility(
    url: str,
    html: str
) -> List[Dict[str, Any]]:
    """
    Prüft Media-Barrierefreiheit einer Seite
    
    Args:
        url: URL der Seite
        html: HTML-Inhalt
        
    Returns:
        Liste von Issues als Dictionaries
    """
    soup = BeautifulSoup(html, 'html.parser')
    issues = await media_checker.check_page(url, soup)
    
    return [issue.to_dict() for issue in issues]
