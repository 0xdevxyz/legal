--
-- PostgreSQL database dump
--

\restrict y7DewYEVPA4TDjcdN5DqVxVAQNam5Z4YTF266A6dc83eH0ZuZVmS6DBSvG39g6D

-- Dumped from database version 15.17
-- Dumped by pg_dump version 15.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: accessibility_alt_text_fixes; Type: TABLE DATA; Schema: public; Owner: complyo_user
--

INSERT INTO public.accessibility_alt_text_fixes (id, site_id, scan_id, user_id, page_url, image_src, image_filename, image_url_hash, suggested_alt, confidence, page_title, surrounding_text, element_html, image_context, status, approved_at, approved_by, rejected_reason, deployed_via, deployed_at, created_at, updated_at) VALUES (1, 'zua-zwickau-de', 'test-scan-channels', NULL, 'https://zua-zwickau.de', 'https://zua-zwickau.de/wp-content/uploads/2023/03/Logo-1024x382.png', 'Logo-1024x382.png', '4d31871a4f3cd005a9253136f887c9dca4dd4813ea9a3955d4b9006562e7580c', 'Stilisiertes Logo mit den Ziffern 7 und 4 in grün und grau auf einem Hintergrund mit Weltkarte und Gitternetzlinien.', 0.900, '', '', '', NULL, 'approved', '2026-06-25 16:27:44.055845', NULL, NULL, NULL, NULL, '2026-06-25 16:27:44.050692', '2026-06-25 16:27:44.055845');


--
-- Data for Name: accessibility_document_fixes; Type: TABLE DATA; Schema: public; Owner: complyo_user
--



--
-- Data for Name: accessibility_fix_packages; Type: TABLE DATA; Schema: public; Owner: complyo_user
--

INSERT INTO public.accessibility_fix_packages (id, user_id, site_id, site_url, fix_package, created_at, updated_at) VALUES (2, '5', 'spedition-mahn-de', 'https://spedition-mahn.de', '{"source": "scan", "summary": {"total_issues": 6}, "manual_guides": [{"description": "11 Bilder haben keinen Alt-Text für Screenreader. Beispiele: http://spedition-mahn-wordpress.web.leapp.studio/w, https://spedition-mahn.de/wp-content/uploads/2026/, https://spedition-mahn.de/wp-content/uploads/2026/.... Alt-Texte sind essentiell für blinde und sehbehinderte Nutzer."}, {"description": "Die Seite verwendet nicht alle wichtigen semantischen HTML5-Elemente: <main>. Diese helfen Screenreader-Nutzern bei der Navigation."}, {"description": "Es wurde keine Barrierefreiheitserklärung gefunden. Ab 28.06.2025 sind B2C-Dienste (Online-Shops, Buchungssysteme, digitale Services) verpflichtet, eine Erklärung zur Barrierefreiheit zu veröffentlichen, die den Konformitätsstatus, bekannte Mängel und einen Feedback-Mechanismus enthält."}, {"description": "Es wurde kein \"Zum Inhalt springen\"-Link gefunden. Tastatur- und Screenreader-Nutzer müssen ohne diesen Link die gesamte Navigation auf jeder Seite durchlaufen, bevor sie zum Hauptinhalt gelangen."}, {"description": "Ein <a> Element hat weder Text-Inhalt noch aria-label/aria-labelledby. Screenreader können das Element nicht identifizieren."}, {"description": "Folgende wichtige Landmark-Regions wurden nicht gefunden: main (role=\"main\"). Diese helfen Screenreader-Nutzern bei der Navigation."}]}', '2026-08-04 20:59:06.84364+00', NULL);


--
-- Data for Name: accessibility_link_fixes; Type: TABLE DATA; Schema: public; Owner: complyo_user
--



--
-- Name: accessibility_alt_text_fixes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: complyo_user
--

SELECT pg_catalog.setval('public.accessibility_alt_text_fixes_id_seq', 2, true);


--
-- Name: accessibility_document_fixes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: complyo_user
--

SELECT pg_catalog.setval('public.accessibility_document_fixes_id_seq', 1, false);


--
-- Name: accessibility_fix_packages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: complyo_user
--

SELECT pg_catalog.setval('public.accessibility_fix_packages_id_seq', 2, true);


--
-- Name: accessibility_link_fixes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: complyo_user
--

SELECT pg_catalog.setval('public.accessibility_link_fixes_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict y7DewYEVPA4TDjcdN5DqVxVAQNam5Z4YTF266A6dc83eH0ZuZVmS6DBSvG39g6D

