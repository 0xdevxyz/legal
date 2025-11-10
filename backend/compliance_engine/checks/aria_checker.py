"""
Erweiterte ARIA-Checks für vollständige Barrierefreiheit
WCAG 2.1 Level AA Kriterien 4.1.2 (Name, Role, Value)
"""

from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)


class ARIAChecker:
    """
    Umfassende ARIA-Validierung
    
    Prüft:
    - ARIA-Labels für interaktive Elemente
    - ARIA-Rollen korrekt verwendet
    - ARIA-Landmark-Regions
    - ARIA-Properties korrekt gesetzt
    - ARIA-States für dynamische Inhalte
    """
    
    # Interaktive Elemente die Labels brauchen
    INTERACTIVE_ELEMENTS = ['button', 'a', 'input', 'select', 'textarea']
    
    # Erforderliche Landmark-Regions
    REQUIRED_LANDMARKS = {
        'banner': 'header',
        'navigation': 'nav',
        'main': 'main',
        'contentinfo': 'footer'
    }
    
    # Valide ARIA-Rollen
    VALID_ROLES = [
        'alert', 'alertdialog', 'article', 'application', 'banner',
        'button', 'checkbox', 'columnheader', 'combobox', 'complementary',
        'contentinfo', 'definition', 'dialog', 'directory', 'document',
        'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
        'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main',
        'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
        'menuitemradio', 'navigation', 'none', 'note', 'option',
        'presentation', 'progressbar', 'radio', 'radiogroup', 'region',
        'row', 'rowgroup', 'rowheader', 'scrollbar', 'search', 'searchbox',
        'separator', 'slider', 'spinbutton', 'status', 'switch', 'tab',
        'table', 'tablist', 'tabpanel', 'term', 'textbox', 'timer',
        'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem'
    ]
    
    def check_aria_compliance(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """
        Führt alle ARIA-Checks durch
        
        Args:
            soup: BeautifulSoup object
            url: Website URL
            
        Returns:
            Liste von Issues
        """
        issues = []
        
        # 1. Interaktive Elemente ohne Label
        issues.extend(self._check_missing_labels(soup, url))
        
        # 2. Landmark-Regions
        issues.extend(self._check_landmarks(soup, url))
        
        # 3. Invalide ARIA-Rollen
        issues.extend(self._check_invalid_roles(soup, url))
        
        # 4. ARIA-Properties
        issues.extend(self._check_aria_properties(soup, url))
        
        # 5. Form-Labels
        issues.extend(self._check_form_labels(soup, url))
        
        # 6. Dynamische Inhalte (aria-live)
        issues.extend(self._check_live_regions(soup, url))
        
        return issues
    
    def _check_missing_labels(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Prüft interaktive Elemente ohne Label"""
        issues = []
        
        for element in self.INTERACTIVE_ELEMENTS:
            for tag in soup.find_all(element):
                has_label = self._has_accessible_name(tag)
                
                if not has_label:
                    issues.append({
                        'category': 'barrierefreiheit',
                        'severity': 'warning',
                        'title': f'{element.upper()} ohne zugängliches Label',
                        'description': (
                            f'Ein <{element}> Element hat weder Text-Inhalt noch '
                            f'aria-label/aria-labelledby. Screenreader können das '
                            f'Element nicht identifizieren.'
                        ),
                        'element_html': str(tag)[:200],
                        'recommendation': self._get_label_recommendation(tag),
                        'legal_basis': 'WCAG 2.1 (4.1.2), BFSG §12',
                        'risk_euro': 1500,
                        'auto_fixable': False,
                        'wcag_criterion': '4.1.2'
                    })
        
        if issues:
            logger.info(f"❌ Gefunden: {len(issues)} Elemente ohne Label")
        
        return issues
    
    def _check_landmarks(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Prüft Landmark-Regions"""
        issues = []
        missing_landmarks = []
        
        for role, element in self.REQUIRED_LANDMARKS.items():
            # Prüfe HTML5-Element oder ARIA-Role
            found = (
                soup.find(element) or 
                soup.find(attrs={'role': role})
            )
            
            if not found:
                missing_landmarks.append(f'{element} (role="{role}")')
        
        if missing_landmarks:
            issues.append({
                'category': 'barrierefreiheit',
                'severity': 'warning',
                'title': f'{len(missing_landmarks)} Landmark-Regions fehlen',
                'description': (
                    f'Folgende wichtige Landmark-Regions wurden nicht gefunden: '
                    f'{", ".join(missing_landmarks)}. Diese helfen Screenreader-Nutzern '
                    f'bei der Navigation.'
                ),
                'recommendation': self._get_landmark_recommendation(missing_landmarks),
                'legal_basis': 'WCAG 2.1 (1.3.1), BFSG §12',
                'risk_euro': 800,
                'auto_fixable': False,
                'wcag_criterion': '1.3.1'
            })
        
        return issues
    
    def _check_invalid_roles(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Prüft auf invalide ARIA-Rollen"""
        issues = []
        
        elements_with_role = soup.find_all(attrs={'role': True})
        invalid_roles = []
        
        for tag in elements_with_role:
            role = tag.get('role', '').strip()
            
            if role and role not in self.VALID_ROLES:
                invalid_roles.append({
                    'role': role,
                    'element': tag.name,
                    'html': str(tag)[:100]
                })
        
        if invalid_roles:
            issues.append({
                'category': 'barrierefreiheit',
                'severity': 'warning',
                'title': f'{len(invalid_roles)} invalide ARIA-Rollen',
                'description': (
                    f'Folgende Elemente haben invalide ARIA-Rollen: '
                    f'{", ".join([r["role"] for r in invalid_roles[:3]])}. '
                    f'Screenreader ignorieren invalide Rollen.'
                ),
                'invalid_roles': invalid_roles,
                'recommendation': (
                    'Verwenden Sie nur valide ARIA-Rollen aus der ARIA 1.2 Spezifikation. '
                    'Siehe: https://www.w3.org/TR/wai-aria-1.2/#role_definitions'
                ),
                'legal_basis': 'WCAG 2.1 (4.1.2), BFSG §12',
                'risk_euro': 1000,
                'auto_fixable': False,
                'wcag_criterion': '4.1.2'
            })
        
        return issues
    
    def _check_aria_properties(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Prüft ARIA-Properties auf Korrektheit"""
        issues = []
        
        # aria-expanded ohne expandable Element
        expandable_elements = soup.find_all(attrs={'aria-expanded': True})
        for tag in expandable_elements:
            aria_controls = tag.get('aria-controls')
            if not aria_controls:
                issues.append({
                    'category': 'barrierefreiheit',
                    'severity': 'info',
                    'title': 'aria-expanded ohne aria-controls',
                    'description': (
                        'Ein Element mit aria-expanded sollte auch aria-controls '
                        'haben, um das gesteuerte Element zu identifizieren.'
                    ),
                    'element_html': str(tag)[:200],
                    'recommendation': 'Fügen Sie aria-controls mit der ID des gesteuerten Elements hinzu.',
                    'legal_basis': 'WCAG 2.1 (4.1.2), Best Practice',
                    'risk_euro': 500,
                    'auto_fixable': False,
                    'wcag_criterion': '4.1.2'
                })
        
        # aria-labelledby mit nicht-existierender ID
        labelledby_elements = soup.find_all(attrs={'aria-labelledby': True})
        for tag in labelledby_elements:
            label_ids = tag.get('aria-labelledby', '').split()
            for label_id in label_ids:
                if not soup.find(attrs={'id': label_id}):
                    issues.append({
                        'category': 'barrierefreiheit',
                        'severity': 'warning',
                        'title': 'aria-labelledby verweist auf nicht-existierende ID',
                        'description': (
                            f'aria-labelledby="{label_id}" verweist auf eine ID, '
                            f'die nicht im DOM existiert.'
                        ),
                        'element_html': str(tag)[:200],
                        'recommendation': f'Stellen Sie sicher, dass ein Element mit id="{label_id}" existiert.',
                        'legal_basis': 'WCAG 2.1 (4.1.2), BFSG §12',
                        'risk_euro': 1000,
                        'auto_fixable': False,
                        'wcag_criterion': '4.1.2'
                    })
        
        return issues
    
    def _check_form_labels(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Prüft Form-Felder auf Labels"""
        issues = []
        unlabeled_inputs = []
        
        # Alle Input-Felder (außer hidden, submit, button)
        form_inputs = soup.find_all('input', type=lambda t: t not in ['hidden', 'submit', 'button'])
        form_inputs.extend(soup.find_all(['textarea', 'select']))
        
        for input_field in form_inputs:
            input_id = input_field.get('id')
            has_label = False
            
            # Prüfe <label for="...">
            if input_id:
                has_label = bool(soup.find('label', attrs={'for': input_id}))
            
            # Prüfe aria-label oder aria-labelledby
            if not has_label:
                has_label = bool(
                    input_field.get('aria-label') or 
                    input_field.get('aria-labelledby')
                )
            
            # Prüfe umschließendes <label>
            if not has_label:
                has_label = bool(input_field.find_parent('label'))
            
            if not has_label:
                unlabeled_inputs.append(str(input_field)[:100])
        
        if unlabeled_inputs:
            issues.append({
                'category': 'barrierefreiheit',
                'severity': 'critical',
                'title': f'{len(unlabeled_inputs)} Formularfelder ohne Label',
                'description': (
                    f'{len(unlabeled_inputs)} Formularfelder haben kein zugeordnetes Label. '
                    f'Screenreader-Nutzer wissen nicht, welche Eingabe erwartet wird.'
                ),
                'examples': unlabeled_inputs[:3],
                'recommendation': (
                    'Fügen Sie jedem Input-Feld ein <label> hinzu oder verwenden Sie '
                    'aria-label/aria-labelledby.'
                ),
                'legal_basis': 'WCAG 2.1 (3.3.2), BFSG §12',
                'risk_euro': 2000,
                'auto_fixable': False,
                'wcag_criterion': '3.3.2'
            })
        
        return issues
    
    def _check_live_regions(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Prüft auf aria-live für dynamische Inhalte"""
        issues = []
        
        # Suche nach potentiell dynamischen Bereichen ohne aria-live
        # (z.B. Status-Meldungen, Alerts, Notifications)
        potential_dynamic = soup.find_all(
            class_=lambda c: c and any(
                keyword in c.lower() 
                for keyword in ['alert', 'notification', 'status', 'message', 'toast']
            )
        )
        
        missing_live = []
        for element in potential_dynamic:
            if not element.get('aria-live') and not element.find(attrs={'aria-live': True}):
                missing_live.append(str(element)[:100])
        
        if missing_live:
            issues.append({
                'category': 'barrierefreiheit',
                'severity': 'info',
                'title': f'{len(missing_live)} dynamische Bereiche ohne aria-live',
                'description': (
                    f'Dynamische Bereiche (Alerts, Notifications) sollten aria-live haben, '
                    f'damit Screenreader Änderungen ankündigen.'
                ),
                'examples': missing_live[:3],
                'recommendation': (
                    'Fügen Sie aria-live="polite" oder aria-live="assertive" hinzu, '
                    'je nach Wichtigkeit der Nachricht.'
                ),
                'legal_basis': 'WCAG 2.1 (4.1.3), BFSG §12',
                'risk_euro': 500,
                'auto_fixable': False,
                'wcag_criterion': '4.1.3'
            })
        
        return issues
    
    def _has_accessible_name(self, tag: Tag) -> bool:
        """Prüft ob Element ein zugängliches Label hat"""
        # Text-Inhalt vorhanden
        if tag.get_text(strip=True):
            return True
        
        # aria-label
        if tag.get('aria-label'):
            return True
        
        # aria-labelledby
        if tag.get('aria-labelledby'):
            return True
        
        # title (nicht ideal, aber besser als nichts)
        if tag.get('title'):
            return True
        
        # Für <a>: href="#" oder leer ist kein valides Label
        if tag.name == 'a':
            href = tag.get('href', '')
            if href and href != '#':
                # Links mit href haben impliziten Namen
                return True
        
        # Für <input>: value kann als Label dienen (z.B. submit buttons)
        if tag.name == 'input':
            input_type = tag.get('type', '').lower()
            if input_type in ['submit', 'button', 'reset']:
                if tag.get('value'):
                    return True
        
        return False
    
    def _get_label_recommendation(self, tag: Tag) -> str:
        """Gibt spezifische Empfehlung für Element-Typ"""
        if tag.name == 'button':
            return (
                'Fügen Sie Text-Inhalt hinzu: <button>Absenden</button> '
                'oder aria-label: <button aria-label="Formular absenden">...</button>'
            )
        elif tag.name == 'a':
            return (
                'Fügen Sie aussagekräftigen Link-Text hinzu: <a href="...">Mehr erfahren</a> '
                'oder aria-label für Icon-Links: <a href="..." aria-label="Profil anzeigen">...</a>'
            )
        elif tag.name == 'input':
            return (
                'Fügen Sie ein <label> hinzu: <label for="email">E-Mail</label><input id="email"> '
                'oder aria-label: <input type="text" aria-label="E-Mail-Adresse">'
            )
        else:
            return f'Fügen Sie ein aria-label zu diesem {tag.name}-Element hinzu.'
    
    def _get_landmark_recommendation(self, missing: List[str]) -> str:
        """Gibt Empfehlung für fehlende Landmarks"""
        recommendations = []
        
        for landmark in missing:
            if 'header' in landmark:
                recommendations.append('<header> für Kopfbereich mit Logo und Navigation')
            elif 'nav' in landmark:
                recommendations.append('<nav> für Hauptnavigation')
            elif 'main' in landmark:
                recommendations.append('<main> für Hauptinhalt der Seite')
            elif 'footer' in landmark:
                recommendations.append('<footer> für Fußbereich')
        
        return 'Fügen Sie folgende Landmark-Elemente hinzu: ' + ', '.join(recommendations)


# Globale Instanz
aria_checker = ARIAChecker()

