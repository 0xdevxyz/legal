--
-- PostgreSQL database dump
--

\restrict CHodISGbMiefA3qZd5OuTZcHtl7ai1ZxAs57jgBGu3xLQDS1YemYGANNFe3r8mb

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
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: scan_frequency; Type: TYPE; Schema: public; Owner: complyo_user
--

CREATE TYPE public.scan_frequency AS ENUM (
    'daily',
    'weekly',
    'monthly',
    'manual'
);


ALTER TYPE public.scan_frequency OWNER TO complyo_user;

--
-- Name: scan_type; Type: TYPE; Schema: public; Owner: complyo_user
--

CREATE TYPE public.scan_type AS ENUM (
    'manual',
    'scheduled',
    'api'
);


ALTER TYPE public.scan_type OWNER TO complyo_user;

--
-- Name: subscription_status; Type: TYPE; Schema: public; Owner: complyo_user
--

CREATE TYPE public.subscription_status AS ENUM (
    'active',
    'cancelled',
    'expired',
    'trial'
);


ALTER TYPE public.subscription_status OWNER TO complyo_user;

--
-- Name: subscription_tier; Type: TYPE; Schema: public; Owner: complyo_user
--

CREATE TYPE public.subscription_tier AS ENUM (
    'free',
    'pro',
    'enterprise'
);


ALTER TYPE public.subscription_tier OWNER TO complyo_user;

--
-- Name: team_role; Type: TYPE; Schema: public; Owner: complyo_user
--

CREATE TYPE public.team_role AS ENUM (
    'owner',
    'admin',
    'member',
    'viewer'
);


ALTER TYPE public.team_role OWNER TO complyo_user;

--
-- Name: website_status; Type: TYPE; Schema: public; Owner: complyo_user
--

CREATE TYPE public.website_status AS ENUM (
    'active',
    'paused',
    'error'
);


ALTER TYPE public.website_status OWNER TO complyo_user;

--
-- Name: archive_old_legal_updates(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.archive_old_legal_updates() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Archiviere Updates älter als 6 Monate die nicht action_required sind
    WITH archived AS (
        INSERT INTO legal_updates_archive
        SELECT *, NOW() as archived_at
        FROM legal_updates
        WHERE published_at < NOW() - INTERVAL '6 months'
        AND (action_required = false OR action_required IS NULL)
        AND id NOT IN (SELECT DISTINCT update_id FROM ai_classification_feedback WHERE created_at >= NOW() - INTERVAL '3 months')
        RETURNING id
    )
    DELETE FROM legal_updates
    WHERE id IN (SELECT id FROM archived)
    RETURNING COUNT(*) INTO archived_count;
    
    RETURN archived_count;
END;
$$;


ALTER FUNCTION public.archive_old_legal_updates() OWNER TO complyo_user;

--
-- Name: FUNCTION archive_old_legal_updates(); Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON FUNCTION public.archive_old_legal_updates() IS 'Archiviert automatisch alte Updates zur Performance-Optimierung';


--
-- Name: check_domain_lock(integer, character varying); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.check_domain_lock(p_user_id integer, p_url character varying) RETURNS TABLE(is_locked boolean, locked_url character varying, needs_new_subscription boolean)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_locked_domain VARCHAR;
    v_plan_type VARCHAR;
BEGIN
    SELECT locked_domain, plan_type 
    INTO v_locked_domain, v_plan_type
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    -- Keine Domain gelockt → OK
    IF v_locked_domain IS NULL THEN
        RETURN QUERY SELECT FALSE, NULL::VARCHAR, FALSE;
        RETURN;
    END IF;
    
    -- Gleiche Domain → OK
    IF v_locked_domain = p_url THEN
        RETURN QUERY SELECT TRUE, v_locked_domain, FALSE;
        RETURN;
    END IF;
    
    -- Andere Domain → Neue Subscription erforderlich (nur bei free/pro)
    IF v_plan_type IN ('free', 'pro') THEN
        RETURN QUERY SELECT TRUE, v_locked_domain, TRUE;
        RETURN;
    END IF;
    
    -- Expert Plan → Mehrere Domains erlaubt
    RETURN QUERY SELECT FALSE, NULL::VARCHAR, FALSE;
END;
$$;


ALTER FUNCTION public.check_domain_lock(p_user_id integer, p_url character varying) OWNER TO complyo_user;

--
-- Name: check_export_limit(integer); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.check_export_limit(p_user_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_exports INTEGER;
    v_max INTEGER;
BEGIN
    SELECT exports_this_month, exports_max 
    INTO v_exports, v_max
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    RETURN v_exports < v_max;
END;
$$;


ALTER FUNCTION public.check_export_limit(p_user_id integer) OWNER TO complyo_user;

--
-- Name: check_fix_limit(integer); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.check_fix_limit(p_user_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_used INTEGER;
    v_limit INTEGER;
BEGIN
    SELECT fixes_used, fixes_limit 
    INTO v_used, v_limit
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    -- NULL-Check
    IF v_used IS NULL THEN v_used := 0; END IF;
    IF v_limit IS NULL THEN v_limit := 1; END IF;
    
    RETURN v_used < v_limit;
END;
$$;


ALTER FUNCTION public.check_fix_limit(p_user_id integer) OWNER TO complyo_user;

--
-- Name: check_website_limit(integer, character varying); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.check_website_limit(p_user_id integer, p_new_url character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_count INTEGER;
    v_max INTEGER;
    v_exists BOOLEAN;
BEGIN
    -- Check ob Website bereits existiert
    SELECT EXISTS(
        SELECT 1 FROM tracked_websites 
        WHERE user_id = p_user_id AND url = p_new_url
    ) INTO v_exists;
    
    IF v_exists THEN
        RETURN TRUE; -- Website bereits tracked, kein Limit-Problem
    END IF;
    
    -- Check Limit
    SELECT websites_count, websites_max 
    INTO v_count, v_max
    FROM user_limits 
    WHERE user_id = p_user_id;
    
    RETURN v_count < v_max;
END;
$$;


ALTER FUNCTION public.check_website_limit(p_user_id integer, p_new_url character varying) OWNER TO complyo_user;

--
-- Name: cleanup_expired_oauth_states(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.cleanup_expired_oauth_states() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM oauth_states WHERE expires_at < CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.cleanup_expired_oauth_states() OWNER TO complyo_user;

--
-- Name: delete_expired_consents(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.delete_expired_consents() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM cookie_consent_logs
    WHERE expires_at < NOW();
    
    RAISE NOTICE 'Deleted expired consent logs (older than 3 years)';
END;
$$;


ALTER FUNCTION public.delete_expired_consents() OWNER TO complyo_user;

--
-- Name: FUNCTION delete_expired_consents(); Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON FUNCTION public.delete_expired_consents() IS 'DSGVO: Löscht Consent-Logs älter als 3 Jahre';


--
-- Name: get_classified_legal_updates(integer, integer, boolean); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.get_classified_legal_updates(p_user_id integer, p_limit integer DEFAULT 6, p_include_info_only boolean DEFAULT false) RETURNS TABLE(id integer, update_type character varying, title text, description text, severity character varying, published_at timestamp without time zone, effective_date timestamp without time zone, url text, action_required boolean, confidence character varying, impact_score numeric, primary_action_type character varying, primary_button_text character varying, primary_button_color character varying, primary_button_icon character varying, reasoning text, user_impact text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        lu.id,
        lu.update_type,
        lu.title,
        lu.description,
        lu.severity,
        lu.published_at,
        lu.effective_date,
        lu.url,
        
        -- Klassifizierung (falls vorhanden)
        -- Konvertiere lu.action_required von TEXT zu BOOLEAN
        COALESCE(ac.action_required, CASE WHEN lu.action_required IS NOT NULL AND lu.action_required::text != '' THEN true ELSE false END) as action_required,
        ac.confidence,
        ac.impact_score,
        ac.primary_action_type,
        ac.primary_button_text,
        ac.primary_button_color,
        ac.primary_button_icon,
        ac.reasoning,
        ac.user_impact
        
    FROM legal_updates lu
    LEFT JOIN ai_classifications ac ON lu.id::varchar = ac.update_id AND (ac.user_id = p_user_id OR ac.user_id IS NULL)
    WHERE (p_include_info_only OR COALESCE(ac.action_required, CASE WHEN lu.action_required IS NOT NULL AND lu.action_required::text != '' THEN true ELSE false END, false) = true)
    ORDER BY 
        COALESCE(ac.action_required, CASE WHEN lu.action_required IS NOT NULL AND lu.action_required::text != '' THEN true ELSE false END, false) DESC,
        COALESCE(ac.impact_score, 5.0) DESC,
        lu.published_at DESC
    LIMIT p_limit;
END;
$$;


ALTER FUNCTION public.get_classified_legal_updates(p_user_id integer, p_limit integer, p_include_info_only boolean) OWNER TO complyo_user;

--
-- Name: FUNCTION get_classified_legal_updates(p_user_id integer, p_limit integer, p_include_info_only boolean); Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON FUNCTION public.get_classified_legal_updates(p_user_id integer, p_limit integer, p_include_info_only boolean) IS 'Holt Legal Updates mit KI-Klassifizierung für einen User';


--
-- Name: get_legal_updates_stats(integer); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.get_legal_updates_stats(p_user_id integer) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_updates', COUNT(*),
        'action_required', SUM(CASE WHEN COALESCE(ac.action_required, lu.action_required, false) THEN 1 ELSE 0 END),
        'critical', SUM(CASE WHEN lu.severity = 'critical' THEN 1 ELSE 0 END),
        'high_impact', SUM(CASE WHEN COALESCE(ac.impact_score, 0) >= 8.0 THEN 1 ELSE 0 END),
        'pending_actions', (
            SELECT COUNT(*) 
            FROM ai_classifications ac2
            LEFT JOIN ai_classification_feedback f ON ac2.id = f.classification_id AND f.user_id = p_user_id
            WHERE (ac2.user_id = p_user_id OR ac2.user_id IS NULL)
            AND ac2.action_required = true
            AND f.id IS NULL
        ),
        'avg_impact_score', AVG(COALESCE(ac.impact_score, 5.0))
    ) INTO result
    FROM legal_updates lu
    LEFT JOIN ai_classifications ac ON lu.id::varchar = ac.update_id AND (ac.user_id = p_user_id OR ac.user_id IS NULL)
    WHERE lu.published_at >= NOW() - INTERVAL '3 months';
    
    RETURN result;
END;
$$;


ALTER FUNCTION public.get_legal_updates_stats(p_user_id integer) OWNER TO complyo_user;

--
-- Name: FUNCTION get_legal_updates_stats(p_user_id integer); Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON FUNCTION public.get_legal_updates_stats(p_user_id integer) IS 'Dashboard-Statistiken für Legal Updates eines Users';


--
-- Name: get_score_history(integer, integer); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.get_score_history(p_website_id integer, p_days integer DEFAULT 30) RETURNS TABLE(date timestamp without time zone, score integer, critical_count integer, scan_type character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        created_at as date,
        compliance_score as score,
        critical_issues_count as critical_count,
        score_history.scan_type
    FROM score_history
    WHERE website_id = p_website_id
      AND created_at >= NOW() - (p_days || ' days')::INTERVAL
    ORDER BY created_at ASC;
END;
$$;


ALTER FUNCTION public.get_score_history(p_website_id integer, p_days integer) OWNER TO complyo_user;

--
-- Name: FUNCTION get_score_history(p_website_id integer, p_days integer); Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON FUNCTION public.get_score_history(p_website_id integer, p_days integer) IS 'Gibt Score-Verlauf für eine Website über die letzten X Tage zurück';


--
-- Name: get_user_modules(integer); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.get_user_modules(p_user_id integer) RETURNS TABLE(module_id character varying, module_name character varying, enabled_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT um.module_id, m.name, um.enabled_at
    FROM user_modules um
    JOIN modules m ON um.module_id = m.id
    WHERE um.user_id = p_user_id
      AND um.status = 'active'
      AND (um.expires_at IS NULL OR um.expires_at > NOW());
END;
$$;


ALTER FUNCTION public.get_user_modules(p_user_id integer) OWNER TO complyo_user;

--
-- Name: increment_banner_revision(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.increment_banner_revision() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Revision erhöhen bei Änderung
    IF (OLD.config IS DISTINCT FROM NEW.config) OR (OLD.services IS DISTINCT FROM NEW.services) THEN
        NEW.revision := OLD.revision + 1;
        NEW.updated_at := NOW();
        
        -- Snapshot in Revisions-Tabelle speichern
        INSERT INTO cookie_banner_revisions (site_id, revision, config_snapshot, services_snapshot, changed_by)
        VALUES (NEW.site_id, NEW.revision, row_to_json(NEW)::jsonb, NEW.services, NEW.user_id);
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.increment_banner_revision() OWNER TO complyo_user;

--
-- Name: increment_fix_counter(integer); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.increment_fix_counter(p_user_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE user_limits
    SET fixes_used = COALESCE(fixes_used, 0) + 1,
        fix_started = TRUE
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION public.increment_fix_counter(p_user_id integer) OWNER TO complyo_user;

--
-- Name: mark_stale_structures(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.mark_stale_structures() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE website_structures
    SET is_stale = TRUE
    WHERE crawled_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
      AND is_stale = FALSE;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$;


ALTER FUNCTION public.mark_stale_structures() OWNER TO complyo_user;

--
-- Name: reset_fix_counter(integer); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.reset_fix_counter(p_user_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE user_limits
    SET fixes_used = 0,
        fixes_limit = 999999
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION public.reset_fix_counter(p_user_id integer) OWNER TO complyo_user;

--
-- Name: reset_monthly_exports(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.reset_monthly_exports() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE user_limits
    SET 
        exports_this_month = 0,
        exports_reset_date = CURRENT_DATE + INTERVAL '1 month'
    WHERE exports_reset_date <= CURRENT_DATE;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$;


ALTER FUNCTION public.reset_monthly_exports() OWNER TO complyo_user;

--
-- Name: set_refund_deadline(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.set_refund_deadline() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.refund_deadline = NEW.started_at + INTERVAL '14 days';
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_refund_deadline() OWNER TO complyo_user;

--
-- Name: trigger_auto_classification(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.trigger_auto_classification() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Markiere für Auto-Klassifizierung (wird von Background-Job verarbeitet)
    NEW.auto_classified := false;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trigger_auto_classification() OWNER TO complyo_user;

--
-- Name: update_documents_timestamp(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.update_documents_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_documents_timestamp() OWNER TO complyo_user;

--
-- Name: update_risk_matrix_timestamp(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.update_risk_matrix_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_risk_matrix_timestamp() OWNER TO complyo_user;

--
-- Name: update_solution_keywords(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.update_solution_keywords() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.keywords = to_tsvector('german', 
        COALESCE(NEW.issue_title, '') || ' ' || 
        COALESCE(NEW.issue_description, '')
    );
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_solution_keywords() OWNER TO complyo_user;

--
-- Name: update_timestamp(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.update_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_timestamp() OWNER TO complyo_user;

--
-- Name: update_tracked_website_after_scan(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.update_tracked_website_after_scan() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Update tracked_websites with latest scan data
    UPDATE tracked_websites
    SET 
        last_score = NEW.compliance_score,
        last_scan_date = NEW.scan_timestamp,
        scan_count = scan_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.website_id;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_tracked_website_after_scan() OWNER TO complyo_user;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO complyo_user;

--
-- Name: update_website_structures_timestamp(); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.update_website_structures_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_website_structures_timestamp() OWNER TO complyo_user;

--
-- Name: user_has_module(integer, character varying); Type: FUNCTION; Schema: public; Owner: complyo_user
--

CREATE FUNCTION public.user_has_module(p_user_id integer, p_module_id character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_modules
        WHERE user_id = p_user_id
          AND module_id = p_module_id
          AND status = 'active'
          AND (expires_at IS NULL OR expires_at > NOW())
    );
END;
$$;


ALTER FUNCTION public.user_has_module(p_user_id integer, p_module_id character varying) OWNER TO complyo_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_solution_cache; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.ai_solution_cache (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    category character varying(100) NOT NULL,
    issue_title character varying(500) NOT NULL,
    issue_description text,
    issue_fingerprint character varying(64) NOT NULL,
    ai_solution text NOT NULL,
    model_used character varying(100) DEFAULT 'moonshotai/kimi-k2-thinking'::character varying,
    generation_date timestamp with time zone DEFAULT now(),
    usage_count integer DEFAULT 0,
    success_rate double precision DEFAULT 0.8,
    last_used_at timestamp with time zone,
    keywords tsvector,
    language character varying(10) DEFAULT 'de'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.ai_solution_cache OWNER TO complyo_user;

--
-- Name: ai_cache_stats; Type: VIEW; Schema: public; Owner: complyo_user
--

CREATE VIEW public.ai_cache_stats AS
 SELECT ai_solution_cache.category,
    count(*) AS total_cached_solutions,
    sum(ai_solution_cache.usage_count) AS total_cache_hits,
    avg(ai_solution_cache.success_rate) AS avg_success_rate,
    max(ai_solution_cache.last_used_at) AS last_cache_hit
   FROM public.ai_solution_cache
  GROUP BY ai_solution_cache.category
  ORDER BY (sum(ai_solution_cache.usage_count)) DESC;


ALTER TABLE public.ai_cache_stats OWNER TO complyo_user;

--
-- Name: ai_classification_feedback; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.ai_classification_feedback (
    id integer NOT NULL,
    user_id integer NOT NULL,
    update_id character varying(255) NOT NULL,
    classification_id integer,
    feedback_type character varying(50) NOT NULL,
    user_action character varying(50),
    time_to_action integer,
    context_data jsonb,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.ai_classification_feedback OWNER TO complyo_user;

--
-- Name: TABLE ai_classification_feedback; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.ai_classification_feedback IS 'User-Feedback zu KI-Klassifizierungen für selbstlernendes System';


--
-- Name: ai_classification_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.ai_classification_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ai_classification_feedback_id_seq OWNER TO complyo_user;

--
-- Name: ai_classification_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.ai_classification_feedback_id_seq OWNED BY public.ai_classification_feedback.id;


--
-- Name: ai_classifications; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.ai_classifications (
    id integer NOT NULL,
    update_id character varying(255) NOT NULL,
    user_id integer,
    action_required boolean DEFAULT false NOT NULL,
    confidence character varying(20) NOT NULL,
    severity character varying(20) NOT NULL,
    impact_score numeric(3,1) NOT NULL,
    primary_action_type character varying(50) NOT NULL,
    primary_action_priority integer NOT NULL,
    primary_action_title text NOT NULL,
    primary_action_description text NOT NULL,
    primary_button_text character varying(100) NOT NULL,
    primary_button_color character varying(20) NOT NULL,
    primary_button_icon character varying(50) NOT NULL,
    estimated_time character varying(50),
    requires_paid_plan boolean DEFAULT false,
    recommended_actions jsonb,
    reasoning text NOT NULL,
    user_impact text NOT NULL,
    consequences_if_ignored text,
    model_version character varying(50) DEFAULT 'v1.0'::character varying,
    classified_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.ai_classifications OWNER TO complyo_user;

--
-- Name: TABLE ai_classifications; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.ai_classifications IS 'KI-gestützte Klassifizierungen von Gesetzesänderungen mit automatischer Handlungsempfehlung';


--
-- Name: ai_classifications_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.ai_classifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ai_classifications_id_seq OWNER TO complyo_user;

--
-- Name: ai_classifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.ai_classifications_id_seq OWNED BY public.ai_classifications.id;


--
-- Name: ai_learning_cycles; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.ai_learning_cycles (
    id integer NOT NULL,
    insights_count integer NOT NULL,
    suggestions jsonb NOT NULL,
    learned_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.ai_learning_cycles OWNER TO complyo_user;

--
-- Name: TABLE ai_learning_cycles; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.ai_learning_cycles IS 'Protokoll der ML-Learning-Cycles für kontinuierliche Verbesserung';


--
-- Name: ai_learning_cycles_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.ai_learning_cycles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ai_learning_cycles_id_seq OWNER TO complyo_user;

--
-- Name: ai_learning_cycles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.ai_learning_cycles_id_seq OWNED BY public.ai_learning_cycles.id;


--
-- Name: alt_text_review_queue; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.alt_text_review_queue (
    id integer NOT NULL,
    user_id integer NOT NULL,
    site_id character varying(255) NOT NULL,
    image_src text NOT NULL,
    suggested_alt text NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    approved_alt text,
    created_at timestamp without time zone DEFAULT now(),
    reviewed_at timestamp without time zone,
    CONSTRAINT alt_text_review_queue_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[])))
);


ALTER TABLE public.alt_text_review_queue OWNER TO complyo_user;

--
-- Name: alt_text_review_queue_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.alt_text_review_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.alt_text_review_queue_id_seq OWNER TO complyo_user;

--
-- Name: alt_text_review_queue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.alt_text_review_queue_id_seq OWNED BY public.alt_text_review_queue.id;


--
-- Name: compliance_fixes; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.compliance_fixes (
    id integer NOT NULL,
    legal_change_id character varying(255),
    user_id integer,
    affected_area character varying(100) NOT NULL,
    fix_type character varying(50) NOT NULL,
    description text NOT NULL,
    code_changes jsonb,
    config_changes jsonb,
    manual_steps text[],
    priority integer DEFAULT 5,
    status character varying(50) DEFAULT 'pending'::character varying,
    applied_at timestamp without time zone,
    applied_by integer,
    result text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.compliance_fixes OWNER TO complyo_user;

--
-- Name: compliance_fixes_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.compliance_fixes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.compliance_fixes_id_seq OWNER TO complyo_user;

--
-- Name: compliance_fixes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.compliance_fixes_id_seq OWNED BY public.compliance_fixes.id;


--
-- Name: compliance_risk_matrix; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.compliance_risk_matrix (
    id integer NOT NULL,
    category character varying(100) NOT NULL,
    issue_type character varying(100) NOT NULL,
    severity character varying(50) DEFAULT 'medium'::character varying,
    fine_min integer DEFAULT 0,
    fine_max integer DEFAULT 0,
    min_risk_euro integer DEFAULT 0,
    max_risk_euro integer DEFAULT 0,
    legal_basis text,
    description text,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.compliance_risk_matrix OWNER TO complyo_user;

--
-- Name: compliance_risk_matrix_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.compliance_risk_matrix_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.compliance_risk_matrix_id_seq OWNER TO complyo_user;

--
-- Name: compliance_risk_matrix_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.compliance_risk_matrix_id_seq OWNED BY public.compliance_risk_matrix.id;


--
-- Name: cookie_banner_configs; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.cookie_banner_configs (
    id integer NOT NULL,
    site_id character varying(255) NOT NULL,
    user_id integer,
    layout character varying(50) DEFAULT 'banner_bottom'::character varying,
    primary_color character varying(7) DEFAULT '#6366f1'::character varying,
    accent_color character varying(7) DEFAULT '#8b5cf6'::character varying,
    text_color character varying(7) DEFAULT '#333333'::character varying,
    bg_color character varying(7) DEFAULT '#ffffff'::character varying,
    button_style character varying(50) DEFAULT 'rounded'::character varying,
    "position" character varying(50) DEFAULT 'bottom'::character varying,
    width_mode character varying(50) DEFAULT 'full'::character varying,
    texts jsonb DEFAULT '{"de": {"title": "🍪 Wir respektieren Ihre Privatsphäre", "imprint": "Impressum", "settings": "Einstellungen", "accept_all": "Alle akzeptieren", "reject_all": "Ablehnen", "description": "Wir verwenden Cookies, um Ihre Erfahrung zu verbessern. Weitere Informationen finden Sie in unserer Datenschutzerklärung.", "privacy_policy": "Datenschutzerklärung", "accept_selected": "Auswahl akzeptieren"}, "en": {"title": "🍪 We respect your privacy", "imprint": "Imprint", "settings": "Settings", "accept_all": "Accept all", "reject_all": "Reject", "description": "We use cookies to enhance your experience. More information in our privacy policy.", "privacy_policy": "Privacy Policy", "accept_selected": "Accept selection"}}'::jsonb NOT NULL,
    services jsonb DEFAULT '[]'::jsonb NOT NULL,
    show_on_pages jsonb DEFAULT '{"all": true, "exclude": []}'::jsonb,
    geo_restriction jsonb DEFAULT '{"enabled": false, "countries": []}'::jsonb,
    auto_block_scripts boolean DEFAULT true,
    respect_dnt boolean DEFAULT true,
    cookie_lifetime_days integer DEFAULT 365,
    show_branding boolean DEFAULT true,
    custom_logo_url text,
    revision integer DEFAULT 1,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    scan_completed_at timestamp without time zone,
    last_scan_url text,
    device_fingerprint character varying(255),
    revision_id integer DEFAULT 1,
    config_hash character varying(64)
);


ALTER TABLE public.cookie_banner_configs OWNER TO complyo_user;

--
-- Name: TABLE cookie_banner_configs; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.cookie_banner_configs IS 'Cookie-Banner-Konfigurationen pro Website';


--
-- Name: COLUMN cookie_banner_configs.show_branding; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.cookie_banner_configs.show_branding IS 'false für Expert Plan (White-Label)';


--
-- Name: COLUMN cookie_banner_configs.revision; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.cookie_banner_configs.revision IS 'Version der Konfiguration - erhöht sich bei Änderungen';


--
-- Name: cookie_banner_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.cookie_banner_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cookie_banner_configs_id_seq OWNER TO complyo_user;

--
-- Name: cookie_banner_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.cookie_banner_configs_id_seq OWNED BY public.cookie_banner_configs.id;


--
-- Name: cookie_banner_revisions; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.cookie_banner_revisions (
    id integer NOT NULL,
    site_id character varying(255) NOT NULL,
    revision integer NOT NULL,
    config_snapshot jsonb NOT NULL,
    services_snapshot jsonb NOT NULL,
    changed_by integer,
    change_reason text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.cookie_banner_revisions OWNER TO complyo_user;

--
-- Name: TABLE cookie_banner_revisions; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.cookie_banner_revisions IS 'Historie aller Banner-Konfigurationen für DSGVO-Nachweis';


--
-- Name: cookie_banner_revisions_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.cookie_banner_revisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cookie_banner_revisions_id_seq OWNER TO complyo_user;

--
-- Name: cookie_banner_revisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.cookie_banner_revisions_id_seq OWNED BY public.cookie_banner_revisions.id;


--
-- Name: cookie_compliance_stats; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.cookie_compliance_stats (
    id integer NOT NULL,
    website_id uuid,
    site_id character varying(255) NOT NULL,
    date date DEFAULT CURRENT_DATE,
    consents_total integer DEFAULT 0,
    consents_accepted integer DEFAULT 0,
    consents_rejected integer DEFAULT 0,
    consents_custom integer DEFAULT 0,
    accepted_all integer DEFAULT 0,
    rejected_all integer DEFAULT 0,
    accepted_partial integer DEFAULT 0,
    unique_visitors integer DEFAULT 0,
    total_impressions integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    accepted_analytics integer DEFAULT 0 NOT NULL,
    accepted_marketing integer DEFAULT 0 NOT NULL,
    accepted_functional integer DEFAULT 0 NOT NULL,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.cookie_compliance_stats OWNER TO complyo_user;

--
-- Name: TABLE cookie_compliance_stats; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.cookie_compliance_stats IS 'Aggregierte Statistiken für Opt-In-Rate Analyse';


--
-- Name: cookie_compliance_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.cookie_compliance_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cookie_compliance_stats_id_seq OWNER TO complyo_user;

--
-- Name: cookie_compliance_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.cookie_compliance_stats_id_seq OWNED BY public.cookie_compliance_stats.id;


--
-- Name: cookie_consent_logs; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.cookie_consent_logs (
    id bigint NOT NULL,
    site_id character varying(255) NOT NULL,
    visitor_id character varying(255) NOT NULL,
    consent_categories jsonb NOT NULL,
    services_accepted jsonb,
    ip_address_hash character varying(64),
    user_agent text,
    revision_id integer NOT NULL,
    language character varying(10),
    banner_shown boolean DEFAULT true,
    "timestamp" timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone DEFAULT (now() + '3 years'::interval),
    device_fingerprint character varying(255),
    action character varying(20) DEFAULT 'accept'::character varying,
    CONSTRAINT cookie_consent_logs_action_check CHECK (((action)::text = ANY ((ARRAY['accept'::character varying, 'revoke'::character varying, 'update'::character varying])::text[])))
);


ALTER TABLE public.cookie_consent_logs OWNER TO complyo_user;

--
-- Name: TABLE cookie_consent_logs; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.cookie_consent_logs IS 'DSGVO-konforme Dokumentation aller Cookie-Consents (3 Jahre Aufbewahrung)';


--
-- Name: COLUMN cookie_consent_logs.visitor_id; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.cookie_consent_logs.visitor_id IS 'Pseudonymisierter Visitor (UUID/Hash) - kein PII';


--
-- Name: COLUMN cookie_consent_logs.ip_address_hash; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.cookie_consent_logs.ip_address_hash IS 'SHA256 Hash der IP-Adresse (nicht reversibel)';


--
-- Name: COLUMN cookie_consent_logs.revision_id; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.cookie_consent_logs.revision_id IS 'Banner-Konfiguration Version - für Revision History';


--
-- Name: cookie_consent_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.cookie_consent_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cookie_consent_logs_id_seq OWNER TO complyo_user;

--
-- Name: cookie_consent_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.cookie_consent_logs_id_seq OWNED BY public.cookie_consent_logs.id;


--
-- Name: cookie_services; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.cookie_services (
    id integer NOT NULL,
    service_key character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    category character varying(50) NOT NULL,
    provider character varying(255),
    template jsonb NOT NULL,
    is_active boolean DEFAULT true,
    plan_required character varying(50) DEFAULT 'ai'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    privacy_url text,
    provider_address text,
    provider_privacy_url text,
    provider_cookie_url text,
    provider_description text,
    script_patterns jsonb DEFAULT '[]'::jsonb,
    iframe_patterns jsonb DEFAULT '[]'::jsonb,
    cookie_names jsonb DEFAULT '[]'::jsonb,
    local_storage_keys jsonb DEFAULT '[]'::jsonb,
    block_method character varying(50) DEFAULT 'script_rewrite'::character varying,
    description text,
    cookies jsonb DEFAULT '[]'::jsonb
);


ALTER TABLE public.cookie_services OWNER TO complyo_user;

--
-- Name: TABLE cookie_services; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.cookie_services IS 'Service-Templates für Cookie-Management (Google Analytics, YouTube, etc.)';


--
-- Name: COLUMN cookie_services.template; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.cookie_services.template IS 'JSON mit: cookies, domains, privacy_policy_url, description, legal_basis, content_blocker_rules';


--
-- Name: cookie_services_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.cookie_services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cookie_services_id_seq OWNER TO complyo_user;

--
-- Name: cookie_services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.cookie_services_id_seq OWNED BY public.cookie_services.id;


--
-- Name: deep_cookie_scans; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.deep_cookie_scans (
    id integer NOT NULL,
    user_id integer NOT NULL,
    website_id character varying(255),
    url text NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    cookies jsonb DEFAULT '[]'::jsonb,
    requests jsonb DEFAULT '[]'::jsonb,
    storage jsonb DEFAULT '{}'::jsonb,
    categorized jsonb DEFAULT '{}'::jsonb,
    total_cookies integer DEFAULT 0,
    unique_services integer DEFAULT 0,
    total_requests integer DEFAULT 0,
    services_detected jsonb DEFAULT '[]'::jsonb,
    scan_duration_seconds integer,
    error_message text,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT deep_cookie_scans_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'running'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);


ALTER TABLE public.deep_cookie_scans OWNER TO complyo_user;

--
-- Name: deep_cookie_scans_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.deep_cookie_scans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.deep_cookie_scans_id_seq OWNER TO complyo_user;

--
-- Name: deep_cookie_scans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.deep_cookie_scans_id_seq OWNED BY public.deep_cookie_scans.id;


--
-- Name: deep_scan_history; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.deep_scan_history (
    id integer NOT NULL,
    scan_id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    event_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.deep_scan_history OWNER TO complyo_user;

--
-- Name: deep_scan_history_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.deep_scan_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.deep_scan_history_id_seq OWNER TO complyo_user;

--
-- Name: deep_scan_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.deep_scan_history_id_seq OWNED BY public.deep_scan_history.id;


--
-- Name: deep_scan_usage; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.deep_scan_usage (
    id integer NOT NULL,
    user_id integer NOT NULL,
    current_month character varying(7) NOT NULL,
    scans_used integer DEFAULT 0,
    scans_limit integer DEFAULT 5,
    last_reset timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.deep_scan_usage OWNER TO complyo_user;

--
-- Name: deep_scan_usage_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.deep_scan_usage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.deep_scan_usage_id_seq OWNER TO complyo_user;

--
-- Name: deep_scan_usage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.deep_scan_usage_id_seq OWNED BY public.deep_scan_usage.id;


--
-- Name: export_history; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.export_history (
    id integer NOT NULL,
    user_id integer NOT NULL,
    fix_id integer NOT NULL,
    exported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    export_format character varying(20) NOT NULL
);


ALTER TABLE public.export_history OWNER TO complyo_user;

--
-- Name: export_history_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.export_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.export_history_id_seq OWNER TO complyo_user;

--
-- Name: export_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.export_history_id_seq OWNED BY public.export_history.id;


--
-- Name: fix_jobs; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.fix_jobs (
    job_id uuid DEFAULT gen_random_uuid() NOT NULL,
    scan_id character varying(255),
    issue_id character varying(255),
    issue_category character varying(100),
    issue_data jsonb,
    status character varying(50) DEFAULT 'pending'::character varying,
    priority integer DEFAULT 0,
    progress_percent integer DEFAULT 0,
    current_step text,
    result text,
    generated_content text,
    implementation_guide text,
    error_message text,
    estimated_duration_seconds integer DEFAULT 60,
    created_at timestamp without time zone DEFAULT now(),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now(),
    user_id integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.fix_jobs OWNER TO complyo_user;

--
-- Name: generated_documents; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.generated_documents (
    id integer NOT NULL,
    user_id integer NOT NULL,
    document_type character varying(50) NOT NULL,
    title character varying(500),
    content text NOT NULL,
    html_content text,
    metadata jsonb DEFAULT '{}'::jsonb,
    status character varying(20) DEFAULT 'active'::character varying,
    language character varying(10) DEFAULT 'de'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    last_reviewed_at timestamp without time zone,
    CONSTRAINT generated_documents_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'archived'::character varying, 'draft'::character varying])::text[])))
);


ALTER TABLE public.generated_documents OWNER TO complyo_user;

--
-- Name: generated_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.generated_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.generated_documents_id_seq OWNER TO complyo_user;

--
-- Name: generated_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.generated_documents_id_seq OWNED BY public.generated_documents.id;


--
-- Name: generated_fixes; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.generated_fixes (
    id integer NOT NULL,
    user_id integer NOT NULL,
    issue_id character varying(100) NOT NULL,
    issue_category character varying(100) NOT NULL,
    fix_type character varying(50) NOT NULL,
    plan_type character varying(20) NOT NULL,
    generated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    exported boolean DEFAULT false,
    exported_at timestamp without time zone,
    export_format character varying(20),
    content_hash character varying(64)
);


ALTER TABLE public.generated_fixes OWNER TO complyo_user;

--
-- Name: generated_fixes_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.generated_fixes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.generated_fixes_id_seq OWNER TO complyo_user;

--
-- Name: generated_fixes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.generated_fixes_id_seq OWNED BY public.generated_fixes.id;


--
-- Name: legal_change_impacts; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.legal_change_impacts (
    id integer NOT NULL,
    legal_change_id character varying(255),
    user_id integer,
    is_affected boolean NOT NULL,
    affected_components text[],
    urgency character varying(50),
    risks text[],
    estimated_effort character varying(100),
    recommendation text,
    analyzed_at timestamp without time zone DEFAULT now(),
    status character varying(50) DEFAULT 'pending'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.legal_change_impacts OWNER TO complyo_user;

--
-- Name: legal_change_impacts_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.legal_change_impacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.legal_change_impacts_id_seq OWNER TO complyo_user;

--
-- Name: legal_change_impacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.legal_change_impacts_id_seq OWNED BY public.legal_change_impacts.id;


--
-- Name: legal_change_notifications; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.legal_change_notifications (
    id integer NOT NULL,
    user_id integer,
    legal_change_id character varying(255),
    notification_type character varying(50) NOT NULL,
    sent_at timestamp without time zone DEFAULT now(),
    read_at timestamp without time zone,
    clicked_at timestamp without time zone,
    status character varying(50) DEFAULT 'sent'::character varying,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.legal_change_notifications OWNER TO complyo_user;

--
-- Name: legal_change_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.legal_change_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.legal_change_notifications_id_seq OWNER TO complyo_user;

--
-- Name: legal_change_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.legal_change_notifications_id_seq OWNED BY public.legal_change_notifications.id;


--
-- Name: legal_changes; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.legal_changes (
    id character varying(255) NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    affected_areas text[] NOT NULL,
    severity character varying(50) NOT NULL,
    effective_date timestamp without time zone NOT NULL,
    source text NOT NULL,
    source_url text,
    requirements text[],
    detected_at timestamp without time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    classification_id integer,
    auto_classified boolean DEFAULT false
);


ALTER TABLE public.legal_changes OWNER TO complyo_user;

--
-- Name: legal_monitoring_logs; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.legal_monitoring_logs (
    id integer NOT NULL,
    scan_date timestamp without time zone DEFAULT now(),
    changes_detected integer DEFAULT 0,
    sources_checked text[],
    status character varying(50) DEFAULT 'completed'::character varying,
    error_message text,
    execution_time_seconds double precision,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.legal_monitoring_logs OWNER TO complyo_user;

--
-- Name: legal_monitoring_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.legal_monitoring_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.legal_monitoring_logs_id_seq OWNER TO complyo_user;

--
-- Name: legal_monitoring_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.legal_monitoring_logs_id_seq OWNED BY public.legal_monitoring_logs.id;


--
-- Name: legal_news; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.legal_news (
    id integer NOT NULL,
    title character varying(500) NOT NULL,
    summary text,
    content text,
    url character varying(500),
    source character varying(255),
    source_url character varying(500),
    published_date timestamp without time zone,
    fetched_date timestamp without time zone DEFAULT now(),
    category character varying(100),
    news_type character varying(50) DEFAULT 'general'::character varying,
    impact_level character varying(50),
    affected_sectors text[],
    tags text[],
    is_featured boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    source_feed character varying(255),
    severity character varying(50),
    keywords text[]
);


ALTER TABLE public.legal_news OWNER TO complyo_user;

--
-- Name: legal_news_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.legal_news_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.legal_news_id_seq OWNER TO complyo_user;

--
-- Name: legal_news_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.legal_news_id_seq OWNED BY public.legal_news.id;


--
-- Name: legal_updates; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.legal_updates (
    id integer NOT NULL,
    update_type character varying(100) NOT NULL,
    title character varying(500) NOT NULL,
    description text,
    severity character varying(50) DEFAULT 'info'::character varying,
    action_required boolean DEFAULT false,
    source character varying(100) DEFAULT 'erecht24'::character varying,
    published_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    effective_date date,
    url text,
    classification_id integer,
    auto_classified boolean DEFAULT false,
    classification_override boolean DEFAULT false
);


ALTER TABLE public.legal_updates OWNER TO complyo_user;

--
-- Name: TABLE legal_updates; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.legal_updates IS 'Gesetzesänderungen und rechtliche Updates von eRecht24 oder manuell';


--
-- Name: COLUMN legal_updates.severity; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.legal_updates.severity IS 'Schweregrad: info (informativ), warning (wichtig), critical (sofortiges Handeln erforderlich)';


--
-- Name: COLUMN legal_updates.action_required; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.legal_updates.action_required IS 'Ob User aktiv werden muss (z.B. Website neu scannen)';


--
-- Name: legal_updates_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.legal_updates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.legal_updates_id_seq OWNER TO complyo_user;

--
-- Name: legal_updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.legal_updates_id_seq OWNED BY public.legal_updates.id;


--
-- Name: legal_updates_archive; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.legal_updates_archive (
    id integer DEFAULT nextval('public.legal_updates_id_seq'::regclass) NOT NULL,
    update_type character varying(100) NOT NULL,
    title character varying(500) NOT NULL,
    description text,
    severity character varying(50) DEFAULT 'info'::character varying,
    action_required boolean DEFAULT false,
    source character varying(100) DEFAULT 'erecht24'::character varying,
    published_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    effective_date date,
    url text,
    classification_id integer,
    auto_classified boolean DEFAULT false,
    classification_override boolean DEFAULT false,
    archived_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.legal_updates_archive OWNER TO complyo_user;

--
-- Name: TABLE legal_updates_archive; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.legal_updates_archive IS 'Archiv für alte Gesetzesänderungen (>6 Monate)';


--
-- Name: COLUMN legal_updates_archive.severity; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.legal_updates_archive.severity IS 'Schweregrad: info (informativ), warning (wichtig), critical (sofortiges Handeln erforderlich)';


--
-- Name: COLUMN legal_updates_archive.action_required; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.legal_updates_archive.action_required IS 'Ob User aktiv werden muss (z.B. Website neu scannen)';


--
-- Name: modules; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.modules (
    id character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    price_monthly numeric(10,2) DEFAULT 19.00 NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.modules OWNER TO complyo_user;

--
-- Name: oauth_providers; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.oauth_providers (
    id integer NOT NULL,
    user_id integer NOT NULL,
    provider character varying(50) NOT NULL,
    provider_user_id character varying(255) NOT NULL,
    provider_email character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.oauth_providers OWNER TO complyo_user;

--
-- Name: TABLE oauth_providers; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.oauth_providers IS 'Verknüpfungen zwischen Usern und OAuth Providern (Google, Apple)';


--
-- Name: COLUMN oauth_providers.provider_user_id; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.oauth_providers.provider_user_id IS 'Unique ID from OAuth provider (Google: sub, Apple: sub)';


--
-- Name: oauth_providers_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.oauth_providers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.oauth_providers_id_seq OWNER TO complyo_user;

--
-- Name: oauth_providers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.oauth_providers_id_seq OWNED BY public.oauth_providers.id;


--
-- Name: oauth_states; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.oauth_states (
    id integer NOT NULL,
    state_token character varying(255) NOT NULL,
    provider character varying(50) NOT NULL,
    redirect_url character varying(512),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp with time zone NOT NULL
);


ALTER TABLE public.oauth_states OWNER TO complyo_user;

--
-- Name: TABLE oauth_states; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.oauth_states IS 'Temporäre State-Tokens für OAuth2 CSRF-Protection';


--
-- Name: oauth_states_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.oauth_states_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.oauth_states_id_seq OWNER TO complyo_user;

--
-- Name: oauth_states_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.oauth_states_id_seq OWNED BY public.oauth_states.id;


--
-- Name: rss_feed_sources; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.rss_feed_sources (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    url character varying(500) NOT NULL,
    category character varying(100),
    is_active boolean DEFAULT true,
    last_fetch timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    keywords text[],
    fetch_frequency_hours integer DEFAULT 24,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.rss_feed_sources OWNER TO complyo_user;

--
-- Name: rss_feed_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.rss_feed_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.rss_feed_sources_id_seq OWNER TO complyo_user;

--
-- Name: rss_feed_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.rss_feed_sources_id_seq OWNED BY public.rss_feed_sources.id;


--
-- Name: scan_history; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.scan_history (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    scan_id character varying(255),
    url character varying(500),
    scan_date timestamp without time zone DEFAULT now(),
    overall_score double precision,
    compliance_score double precision,
    legal_score double precision,
    cookie_score double precision,
    accessibility_score double precision,
    privacy_score double precision,
    issues_count integer DEFAULT 0,
    critical_issues integer DEFAULT 0,
    warnings_count integer DEFAULT 0,
    results jsonb,
    scan_data jsonb,
    created_at timestamp without time zone DEFAULT now(),
    user_id integer,
    website_id integer,
    website_name character varying(255),
    scan_timestamp timestamp without time zone DEFAULT now(),
    total_risk_euro numeric(10,2) DEFAULT 0,
    warning_issues integer DEFAULT 0,
    total_issues integer DEFAULT 0,
    scan_duration_ms integer DEFAULT 0
);


ALTER TABLE public.scan_history OWNER TO complyo_user;

--
-- Name: TABLE scan_history; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON TABLE public.scan_history IS 'Vollständige Historie aller Compliance-Scans mit JSONB-Speicherung';


--
-- Name: COLUMN scan_history.scan_data; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON COLUMN public.scan_history.scan_data IS 'Vollständiger Scan-Output als JSON (issues, recommendations, etc.)';


--
-- Name: score_history; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.score_history (
    id integer NOT NULL,
    website_id uuid,
    user_id integer,
    overall_score double precision,
    pillar_scores jsonb,
    scan_date timestamp without time zone DEFAULT now(),
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.score_history OWNER TO complyo_user;

--
-- Name: score_history_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.score_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.score_history_id_seq OWNER TO complyo_user;

--
-- Name: score_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.score_history_id_seq OWNED BY public.score_history.id;


--
-- Name: stripe_customers; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.stripe_customers (
    user_id integer NOT NULL,
    stripe_customer_id character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.stripe_customers OWNER TO complyo_user;

--
-- Name: subscription_plans; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.subscription_plans (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    price_monthly numeric(10,2),
    price_yearly numeric(10,2),
    stripe_price_id_monthly character varying(255),
    stripe_price_id_yearly character varying(255),
    stripe_product_id character varying(255),
    features jsonb,
    max_websites integer,
    max_scans_per_month integer,
    max_team_members integer,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    plan_type character varying(30)
);


ALTER TABLE public.subscription_plans OWNER TO complyo_user;

--
-- Name: subscription_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.subscription_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscription_plans_id_seq OWNER TO complyo_user;

--
-- Name: subscription_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.subscription_plans_id_seq OWNED BY public.subscription_plans.id;


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.subscriptions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    stripe_subscription_id character varying(255),
    stripe_customer_id character varying(255),
    plan_type character varying(20) NOT NULL,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fix_first_used_at timestamp without time zone,
    refund_eligible boolean DEFAULT true,
    refund_deadline timestamp without time zone,
    refund_requested_at timestamp without time zone,
    refund_processed_at timestamp without time zone,
    refund_stripe_id character varying(255),
    status character varying(50) DEFAULT 'active'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.subscriptions OWNER TO complyo_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscriptions_id_seq OWNER TO complyo_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.subscriptions_id_seq OWNED BY public.subscriptions.id;


--
-- Name: tracked_websites; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.tracked_websites (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    url character varying(500) NOT NULL,
    name character varying(255),
    last_scan_date timestamp without time zone,
    last_score double precision,
    scan_frequency character varying(50) DEFAULT 'weekly'::character varying,
    auto_fix_enabled boolean DEFAULT false,
    notification_enabled boolean DEFAULT true,
    status character varying(50) DEFAULT 'active'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    scan_count integer DEFAULT 0,
    is_primary boolean DEFAULT false,
    user_id integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.tracked_websites OWNER TO complyo_user;

--
-- Name: user_limits; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.user_limits (
    user_id integer NOT NULL,
    plan_type character varying(20) DEFAULT 'ai'::character varying NOT NULL,
    websites_count integer DEFAULT 0,
    websites_max integer DEFAULT 1,
    exports_this_month integer DEFAULT 0,
    exports_max integer DEFAULT 10,
    exports_reset_date date,
    fix_started boolean DEFAULT false,
    money_back_eligible boolean DEFAULT true,
    subscription_start timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fixes_used integer DEFAULT 0,
    fixes_limit integer DEFAULT 1,
    locked_domain character varying(500) DEFAULT NULL::character varying
);


ALTER TABLE public.user_limits OWNER TO complyo_user;

--
-- Name: user_modules; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.user_modules (
    id integer NOT NULL,
    user_id integer NOT NULL,
    module_id character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying,
    stripe_subscription_id character varying(255),
    enabled_at timestamp with time zone DEFAULT now(),
    cancelled_at timestamp with time zone,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_modules_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'cancelled'::character varying, 'expired'::character varying])::text[])))
);


ALTER TABLE public.user_modules OWNER TO complyo_user;

--
-- Name: user_modules_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.user_modules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_modules_id_seq OWNER TO complyo_user;

--
-- Name: user_modules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.user_modules_id_seq OWNED BY public.user_modules.id;


--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.user_sessions (
    id integer NOT NULL,
    user_id integer,
    refresh_token character varying(512) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_sessions OWNER TO complyo_user;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.user_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_sessions_id_seq OWNER TO complyo_user;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.user_sessions_id_seq OWNED BY public.user_sessions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(255),
    company character varying(255),
    is_active boolean DEFAULT true,
    is_verified boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    onboarding_completed boolean DEFAULT false,
    plan_type character varying(50) DEFAULT 'free'::character varying
);


ALTER TABLE public.users OWNER TO complyo_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: complyo_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO complyo_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: complyo_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: v_classification_performance; Type: VIEW; Schema: public; Owner: complyo_user
--

CREATE VIEW public.v_classification_performance AS
SELECT
    NULL::integer AS id,
    NULL::character varying(255) AS update_id,
    NULL::boolean AS action_required,
    NULL::character varying(20) AS confidence,
    NULL::character varying(20) AS severity,
    NULL::numeric(3,1) AS impact_score,
    NULL::character varying(50) AS primary_action_type,
    NULL::bigint AS total_feedback,
    NULL::bigint AS positive_feedback,
    NULL::bigint AS negative_feedback,
    NULL::bigint AS engaged_users,
    NULL::numeric AS avg_time_to_action,
    NULL::double precision AS performance_score,
    NULL::timestamp with time zone AS classified_at;


ALTER TABLE public.v_classification_performance OWNER TO complyo_user;

--
-- Name: v_consent_rates; Type: VIEW; Schema: public; Owner: complyo_user
--

CREATE VIEW public.v_consent_rates AS
 SELECT cookie_consent_logs.site_id,
    date(cookie_consent_logs."timestamp") AS date,
    count(*) AS total_consents,
    sum(
        CASE
            WHEN (((cookie_consent_logs.consent_categories ->> 'analytics'::text))::boolean = true) THEN 1
            ELSE 0
        END) AS analytics_accepted,
    sum(
        CASE
            WHEN (((cookie_consent_logs.consent_categories ->> 'marketing'::text))::boolean = true) THEN 1
            ELSE 0
        END) AS marketing_accepted,
    sum(
        CASE
            WHEN (((cookie_consent_logs.consent_categories ->> 'functional'::text))::boolean = true) THEN 1
            ELSE 0
        END) AS functional_accepted,
    round(((100.0 * (sum(
        CASE
            WHEN (((cookie_consent_logs.consent_categories ->> 'analytics'::text))::boolean = true) THEN 1
            ELSE 0
        END))::numeric) / (count(*))::numeric), 2) AS analytics_rate,
    round(((100.0 * (sum(
        CASE
            WHEN (((cookie_consent_logs.consent_categories ->> 'marketing'::text))::boolean = true) THEN 1
            ELSE 0
        END))::numeric) / (count(*))::numeric), 2) AS marketing_rate
   FROM public.cookie_consent_logs
  GROUP BY cookie_consent_logs.site_id, (date(cookie_consent_logs."timestamp"));


ALTER TABLE public.v_consent_rates OWNER TO complyo_user;

--
-- Name: VIEW v_consent_rates; Type: COMMENT; Schema: public; Owner: complyo_user
--

COMMENT ON VIEW public.v_consent_rates IS 'Consent-Raten pro Website und Tag';


--
-- Name: v_learning_insights; Type: VIEW; Schema: public; Owner: complyo_user
--

CREATE VIEW public.v_learning_insights AS
 SELECT ac.primary_action_type,
    ac.severity,
    ac.confidence,
    count(*) AS total_classifications,
    avg(ac.impact_score) AS avg_impact_score,
    count(f.id) AS total_feedback,
    avg(
        CASE
            WHEN ((f.feedback_type)::text = ANY ((ARRAY['explicit_helpful'::character varying, 'action_completed'::character varying])::text[])) THEN 1
            ELSE 0
        END) AS success_rate,
    avg(f.time_to_action) AS avg_response_time,
    ((sum(
        CASE
            WHEN (f.user_action IS NOT NULL) THEN 1
            ELSE 0
        END))::double precision / (NULLIF(count(DISTINCT f.user_id), 0))::double precision) AS engagement_rate
   FROM (public.ai_classifications ac
     LEFT JOIN public.ai_classification_feedback f ON ((ac.id = f.classification_id)))
  WHERE (ac.classified_at >= (now() - '30 days'::interval))
  GROUP BY ac.primary_action_type, ac.severity, ac.confidence
 HAVING (count(*) >= 5)
  ORDER BY (avg(
        CASE
            WHEN ((f.feedback_type)::text = ANY ((ARRAY['explicit_helpful'::character varying, 'action_completed'::character varying])::text[])) THEN 1
            ELSE 0
        END)) DESC NULLS LAST;


ALTER TABLE public.v_learning_insights OWNER TO complyo_user;

--
-- Name: waitlist_leads; Type: TABLE; Schema: public; Owner: complyo_user
--

CREATE TABLE public.waitlist_leads (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    name character varying(120),
    phone character varying(40),
    consent_given_at timestamp with time zone NOT NULL,
    confirmed_at timestamp with time zone,
    confirm_token character varying(64),
    confirm_token_expires_at timestamp with time zone,
    source character varying(40) DEFAULT 'early-access'::character varying NOT NULL,
    ip_hash character varying(64),
    user_agent character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.waitlist_leads OWNER TO complyo_user;

--
-- Name: ai_classification_feedback id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_classification_feedback ALTER COLUMN id SET DEFAULT nextval('public.ai_classification_feedback_id_seq'::regclass);


--
-- Name: ai_classifications id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_classifications ALTER COLUMN id SET DEFAULT nextval('public.ai_classifications_id_seq'::regclass);


--
-- Name: ai_learning_cycles id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_learning_cycles ALTER COLUMN id SET DEFAULT nextval('public.ai_learning_cycles_id_seq'::regclass);


--
-- Name: alt_text_review_queue id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.alt_text_review_queue ALTER COLUMN id SET DEFAULT nextval('public.alt_text_review_queue_id_seq'::regclass);


--
-- Name: compliance_fixes id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.compliance_fixes ALTER COLUMN id SET DEFAULT nextval('public.compliance_fixes_id_seq'::regclass);


--
-- Name: compliance_risk_matrix id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.compliance_risk_matrix ALTER COLUMN id SET DEFAULT nextval('public.compliance_risk_matrix_id_seq'::regclass);


--
-- Name: cookie_banner_configs id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_configs ALTER COLUMN id SET DEFAULT nextval('public.cookie_banner_configs_id_seq'::regclass);


--
-- Name: cookie_banner_revisions id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_revisions ALTER COLUMN id SET DEFAULT nextval('public.cookie_banner_revisions_id_seq'::regclass);


--
-- Name: cookie_compliance_stats id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_compliance_stats ALTER COLUMN id SET DEFAULT nextval('public.cookie_compliance_stats_id_seq'::regclass);


--
-- Name: cookie_consent_logs id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_consent_logs ALTER COLUMN id SET DEFAULT nextval('public.cookie_consent_logs_id_seq'::regclass);


--
-- Name: cookie_services id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_services ALTER COLUMN id SET DEFAULT nextval('public.cookie_services_id_seq'::regclass);


--
-- Name: deep_cookie_scans id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_cookie_scans ALTER COLUMN id SET DEFAULT nextval('public.deep_cookie_scans_id_seq'::regclass);


--
-- Name: deep_scan_history id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_scan_history ALTER COLUMN id SET DEFAULT nextval('public.deep_scan_history_id_seq'::regclass);


--
-- Name: deep_scan_usage id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_scan_usage ALTER COLUMN id SET DEFAULT nextval('public.deep_scan_usage_id_seq'::regclass);


--
-- Name: export_history id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.export_history ALTER COLUMN id SET DEFAULT nextval('public.export_history_id_seq'::regclass);


--
-- Name: generated_documents id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.generated_documents ALTER COLUMN id SET DEFAULT nextval('public.generated_documents_id_seq'::regclass);


--
-- Name: generated_fixes id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.generated_fixes ALTER COLUMN id SET DEFAULT nextval('public.generated_fixes_id_seq'::regclass);


--
-- Name: legal_change_impacts id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_impacts ALTER COLUMN id SET DEFAULT nextval('public.legal_change_impacts_id_seq'::regclass);


--
-- Name: legal_change_notifications id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_notifications ALTER COLUMN id SET DEFAULT nextval('public.legal_change_notifications_id_seq'::regclass);


--
-- Name: legal_monitoring_logs id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_monitoring_logs ALTER COLUMN id SET DEFAULT nextval('public.legal_monitoring_logs_id_seq'::regclass);


--
-- Name: legal_news id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_news ALTER COLUMN id SET DEFAULT nextval('public.legal_news_id_seq'::regclass);


--
-- Name: legal_updates id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_updates ALTER COLUMN id SET DEFAULT nextval('public.legal_updates_id_seq'::regclass);


--
-- Name: oauth_providers id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.oauth_providers ALTER COLUMN id SET DEFAULT nextval('public.oauth_providers_id_seq'::regclass);


--
-- Name: oauth_states id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.oauth_states ALTER COLUMN id SET DEFAULT nextval('public.oauth_states_id_seq'::regclass);


--
-- Name: rss_feed_sources id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.rss_feed_sources ALTER COLUMN id SET DEFAULT nextval('public.rss_feed_sources_id_seq'::regclass);


--
-- Name: score_history id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.score_history ALTER COLUMN id SET DEFAULT nextval('public.score_history_id_seq'::regclass);


--
-- Name: subscription_plans id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.subscription_plans ALTER COLUMN id SET DEFAULT nextval('public.subscription_plans_id_seq'::regclass);


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id SET DEFAULT nextval('public.subscriptions_id_seq'::regclass);


--
-- Name: user_modules id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_modules ALTER COLUMN id SET DEFAULT nextval('public.user_modules_id_seq'::regclass);


--
-- Name: user_sessions id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_sessions ALTER COLUMN id SET DEFAULT nextval('public.user_sessions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: ai_classification_feedback ai_classification_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_classification_feedback
    ADD CONSTRAINT ai_classification_feedback_pkey PRIMARY KEY (id);


--
-- Name: ai_classifications ai_classifications_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_classifications
    ADD CONSTRAINT ai_classifications_pkey PRIMARY KEY (id);


--
-- Name: ai_classifications ai_classifications_update_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_classifications
    ADD CONSTRAINT ai_classifications_update_id_user_id_key UNIQUE (update_id, user_id);


--
-- Name: ai_learning_cycles ai_learning_cycles_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_learning_cycles
    ADD CONSTRAINT ai_learning_cycles_pkey PRIMARY KEY (id);


--
-- Name: ai_solution_cache ai_solution_cache_issue_fingerprint_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_solution_cache
    ADD CONSTRAINT ai_solution_cache_issue_fingerprint_key UNIQUE (issue_fingerprint);


--
-- Name: ai_solution_cache ai_solution_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_solution_cache
    ADD CONSTRAINT ai_solution_cache_pkey PRIMARY KEY (id);


--
-- Name: alt_text_review_queue alt_text_review_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.alt_text_review_queue
    ADD CONSTRAINT alt_text_review_queue_pkey PRIMARY KEY (id);


--
-- Name: compliance_fixes compliance_fixes_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.compliance_fixes
    ADD CONSTRAINT compliance_fixes_pkey PRIMARY KEY (id);


--
-- Name: compliance_risk_matrix compliance_risk_matrix_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.compliance_risk_matrix
    ADD CONSTRAINT compliance_risk_matrix_pkey PRIMARY KEY (id);


--
-- Name: cookie_banner_configs cookie_banner_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_configs
    ADD CONSTRAINT cookie_banner_configs_pkey PRIMARY KEY (id);


--
-- Name: cookie_banner_configs cookie_banner_configs_site_id_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_configs
    ADD CONSTRAINT cookie_banner_configs_site_id_key UNIQUE (site_id);


--
-- Name: cookie_banner_revisions cookie_banner_revisions_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_revisions
    ADD CONSTRAINT cookie_banner_revisions_pkey PRIMARY KEY (id);


--
-- Name: cookie_banner_revisions cookie_banner_revisions_site_id_revision_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_revisions
    ADD CONSTRAINT cookie_banner_revisions_site_id_revision_key UNIQUE (site_id, revision);


--
-- Name: cookie_compliance_stats cookie_compliance_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_compliance_stats
    ADD CONSTRAINT cookie_compliance_stats_pkey PRIMARY KEY (id);


--
-- Name: cookie_consent_logs cookie_consent_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_consent_logs
    ADD CONSTRAINT cookie_consent_logs_pkey PRIMARY KEY (id);


--
-- Name: cookie_services cookie_services_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_services
    ADD CONSTRAINT cookie_services_pkey PRIMARY KEY (id);


--
-- Name: cookie_services cookie_services_service_key_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_services
    ADD CONSTRAINT cookie_services_service_key_key UNIQUE (service_key);


--
-- Name: deep_cookie_scans deep_cookie_scans_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_cookie_scans
    ADD CONSTRAINT deep_cookie_scans_pkey PRIMARY KEY (id);


--
-- Name: deep_scan_history deep_scan_history_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_scan_history
    ADD CONSTRAINT deep_scan_history_pkey PRIMARY KEY (id);


--
-- Name: deep_scan_usage deep_scan_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_scan_usage
    ADD CONSTRAINT deep_scan_usage_pkey PRIMARY KEY (id);


--
-- Name: deep_scan_usage deep_scan_usage_user_id_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_scan_usage
    ADD CONSTRAINT deep_scan_usage_user_id_key UNIQUE (user_id);


--
-- Name: export_history export_history_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.export_history
    ADD CONSTRAINT export_history_pkey PRIMARY KEY (id);


--
-- Name: fix_jobs fix_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.fix_jobs
    ADD CONSTRAINT fix_jobs_pkey PRIMARY KEY (job_id);


--
-- Name: generated_documents generated_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.generated_documents
    ADD CONSTRAINT generated_documents_pkey PRIMARY KEY (id);


--
-- Name: generated_fixes generated_fixes_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.generated_fixes
    ADD CONSTRAINT generated_fixes_pkey PRIMARY KEY (id);


--
-- Name: legal_change_impacts legal_change_impacts_legal_change_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_impacts
    ADD CONSTRAINT legal_change_impacts_legal_change_id_user_id_key UNIQUE (legal_change_id, user_id);


--
-- Name: legal_change_impacts legal_change_impacts_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_impacts
    ADD CONSTRAINT legal_change_impacts_pkey PRIMARY KEY (id);


--
-- Name: legal_change_notifications legal_change_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_notifications
    ADD CONSTRAINT legal_change_notifications_pkey PRIMARY KEY (id);


--
-- Name: legal_changes legal_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_changes
    ADD CONSTRAINT legal_changes_pkey PRIMARY KEY (id);


--
-- Name: legal_monitoring_logs legal_monitoring_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_monitoring_logs
    ADD CONSTRAINT legal_monitoring_logs_pkey PRIMARY KEY (id);


--
-- Name: legal_news legal_news_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_news
    ADD CONSTRAINT legal_news_pkey PRIMARY KEY (id);


--
-- Name: legal_updates_archive legal_updates_archive_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_updates_archive
    ADD CONSTRAINT legal_updates_archive_pkey PRIMARY KEY (id);


--
-- Name: legal_updates legal_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_updates
    ADD CONSTRAINT legal_updates_pkey PRIMARY KEY (id);


--
-- Name: modules modules_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_pkey PRIMARY KEY (id);


--
-- Name: oauth_providers oauth_providers_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.oauth_providers
    ADD CONSTRAINT oauth_providers_pkey PRIMARY KEY (id);


--
-- Name: oauth_providers oauth_providers_provider_provider_user_id_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.oauth_providers
    ADD CONSTRAINT oauth_providers_provider_provider_user_id_key UNIQUE (provider, provider_user_id);


--
-- Name: oauth_states oauth_states_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.oauth_states
    ADD CONSTRAINT oauth_states_pkey PRIMARY KEY (id);


--
-- Name: oauth_states oauth_states_state_token_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.oauth_states
    ADD CONSTRAINT oauth_states_state_token_key UNIQUE (state_token);


--
-- Name: rss_feed_sources rss_feed_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.rss_feed_sources
    ADD CONSTRAINT rss_feed_sources_pkey PRIMARY KEY (id);


--
-- Name: rss_feed_sources rss_feed_sources_url_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.rss_feed_sources
    ADD CONSTRAINT rss_feed_sources_url_key UNIQUE (url);


--
-- Name: scan_history scan_history_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.scan_history
    ADD CONSTRAINT scan_history_pkey PRIMARY KEY (id);


--
-- Name: score_history score_history_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.score_history
    ADD CONSTRAINT score_history_pkey PRIMARY KEY (id);


--
-- Name: stripe_customers stripe_customers_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.stripe_customers
    ADD CONSTRAINT stripe_customers_pkey PRIMARY KEY (user_id);


--
-- Name: stripe_customers stripe_customers_stripe_customer_id_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.stripe_customers
    ADD CONSTRAINT stripe_customers_stripe_customer_id_key UNIQUE (stripe_customer_id);


--
-- Name: subscription_plans subscription_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.subscription_plans
    ADD CONSTRAINT subscription_plans_pkey PRIMARY KEY (id);


--
-- Name: subscription_plans subscription_plans_plan_type_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.subscription_plans
    ADD CONSTRAINT subscription_plans_plan_type_key UNIQUE (plan_type);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: tracked_websites tracked_websites_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.tracked_websites
    ADD CONSTRAINT tracked_websites_pkey PRIMARY KEY (id);


--
-- Name: tracked_websites tracked_websites_url_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.tracked_websites
    ADD CONSTRAINT tracked_websites_url_key UNIQUE (url);


--
-- Name: user_limits user_limits_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_limits
    ADD CONSTRAINT user_limits_pkey PRIMARY KEY (user_id);


--
-- Name: user_modules user_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_modules
    ADD CONSTRAINT user_modules_pkey PRIMARY KEY (id);


--
-- Name: user_modules user_modules_user_id_module_id_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_modules
    ADD CONSTRAINT user_modules_user_id_module_id_key UNIQUE (user_id, module_id);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_refresh_token_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_refresh_token_key UNIQUE (refresh_token);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: waitlist_leads waitlist_leads_confirm_token_unique; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.waitlist_leads
    ADD CONSTRAINT waitlist_leads_confirm_token_unique UNIQUE (confirm_token);


--
-- Name: waitlist_leads waitlist_leads_email_unique; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.waitlist_leads
    ADD CONSTRAINT waitlist_leads_email_unique UNIQUE (email);


--
-- Name: waitlist_leads waitlist_leads_pkey; Type: CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.waitlist_leads
    ADD CONSTRAINT waitlist_leads_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_cache_category; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_cache_category ON public.ai_solution_cache USING btree (category);


--
-- Name: idx_ai_cache_fingerprint; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_cache_fingerprint ON public.ai_solution_cache USING btree (issue_fingerprint);


--
-- Name: idx_ai_cache_keywords; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_cache_keywords ON public.ai_solution_cache USING gin (keywords);


--
-- Name: idx_ai_cache_last_used; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_cache_last_used ON public.ai_solution_cache USING btree (last_used_at DESC);


--
-- Name: idx_ai_cache_success; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_cache_success ON public.ai_solution_cache USING btree (success_rate DESC);


--
-- Name: idx_ai_cache_usage; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_cache_usage ON public.ai_solution_cache USING btree (usage_count DESC);


--
-- Name: idx_ai_classifications_action_required; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_classifications_action_required ON public.ai_classifications USING btree (action_required);


--
-- Name: idx_ai_classifications_classified_at; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_classifications_classified_at ON public.ai_classifications USING btree (classified_at DESC);


--
-- Name: idx_ai_classifications_severity; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_classifications_severity ON public.ai_classifications USING btree (severity);


--
-- Name: idx_ai_classifications_update; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_classifications_update ON public.ai_classifications USING btree (update_id);


--
-- Name: idx_ai_classifications_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_ai_classifications_user ON public.ai_classifications USING btree (user_id);


--
-- Name: idx_alt_text_queue_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_alt_text_queue_user ON public.alt_text_review_queue USING btree (user_id, status);


--
-- Name: idx_banner_config_site; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_banner_config_site ON public.cookie_banner_configs USING btree (site_id);


--
-- Name: idx_banner_config_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_banner_config_user ON public.cookie_banner_configs USING btree (user_id);


--
-- Name: idx_consent_expires; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_consent_expires ON public.cookie_consent_logs USING btree (expires_at);


--
-- Name: idx_consent_site_visitor; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_consent_site_visitor ON public.cookie_consent_logs USING btree (site_id, visitor_id);


--
-- Name: idx_consent_timestamp; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_consent_timestamp ON public.cookie_consent_logs USING btree ("timestamp");


--
-- Name: idx_cookie_banner_configs_scan; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_cookie_banner_configs_scan ON public.cookie_banner_configs USING btree (scan_completed_at);


--
-- Name: idx_cookie_consent_logs_timestamp; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_cookie_consent_logs_timestamp ON public.cookie_consent_logs USING btree ("timestamp");


--
-- Name: idx_cookie_services_block_method; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_cookie_services_block_method ON public.cookie_services USING btree (block_method);


--
-- Name: idx_cookie_stats_site; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE UNIQUE INDEX idx_cookie_stats_site ON public.cookie_compliance_stats USING btree (site_id, date);


--
-- Name: idx_deep_scans_created; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_deep_scans_created ON public.deep_cookie_scans USING btree (created_at);


--
-- Name: idx_deep_scans_status; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_deep_scans_status ON public.deep_cookie_scans USING btree (status);


--
-- Name: idx_deep_scans_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_deep_scans_user ON public.deep_cookie_scans USING btree (user_id);


--
-- Name: idx_deep_scans_website; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_deep_scans_website ON public.deep_cookie_scans USING btree (website_id);


--
-- Name: idx_export_history_month; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_export_history_month ON public.export_history USING btree (exported_at);


--
-- Name: idx_export_history_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_export_history_user ON public.export_history USING btree (user_id);


--
-- Name: idx_feedback_classification; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_feedback_classification ON public.ai_classification_feedback USING btree (classification_id);


--
-- Name: idx_feedback_created; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_feedback_created ON public.ai_classification_feedback USING btree (created_at DESC);


--
-- Name: idx_feedback_type; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_feedback_type ON public.ai_classification_feedback USING btree (feedback_type);


--
-- Name: idx_feedback_update; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_feedback_update ON public.ai_classification_feedback USING btree (update_id);


--
-- Name: idx_feedback_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_feedback_user ON public.ai_classification_feedback USING btree (user_id);


--
-- Name: idx_fix_jobs_created_at; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_fix_jobs_created_at ON public.fix_jobs USING btree (created_at);


--
-- Name: idx_fix_jobs_priority; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_fix_jobs_priority ON public.fix_jobs USING btree (priority DESC);


--
-- Name: idx_fix_jobs_status; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_fix_jobs_status ON public.fix_jobs USING btree (status);


--
-- Name: idx_fixes_category; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_fixes_category ON public.generated_fixes USING btree (issue_category);


--
-- Name: idx_fixes_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_fixes_user ON public.generated_fixes USING btree (user_id);


--
-- Name: idx_gen_docs_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_gen_docs_user ON public.generated_documents USING btree (user_id, document_type);


--
-- Name: idx_history_scan; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_history_scan ON public.deep_scan_history USING btree (scan_id);


--
-- Name: idx_learning_cycles_learned_at; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_learning_cycles_learned_at ON public.ai_learning_cycles USING btree (learned_at DESC);


--
-- Name: idx_legal_news_active; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_news_active ON public.legal_news USING btree (is_active);


--
-- Name: idx_legal_news_category; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_news_category ON public.legal_news USING btree (category);


--
-- Name: idx_legal_news_featured; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_news_featured ON public.legal_news USING btree (is_featured);


--
-- Name: idx_legal_news_published; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_news_published ON public.legal_news USING btree (published_date DESC);


--
-- Name: idx_legal_news_published_date; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_news_published_date ON public.legal_news USING btree (published_date);


--
-- Name: idx_legal_news_source; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_news_source ON public.legal_news USING btree (source);


--
-- Name: idx_legal_updates_action_required; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_updates_action_required ON public.legal_updates USING btree (action_required);


--
-- Name: idx_legal_updates_archive_archived_at; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_updates_archive_archived_at ON public.legal_updates_archive USING btree (archived_at DESC);


--
-- Name: idx_legal_updates_published; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_updates_published ON public.legal_updates USING btree (published_at DESC);


--
-- Name: idx_legal_updates_published_at; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_updates_published_at ON public.legal_updates USING btree (published_at DESC);


--
-- Name: idx_legal_updates_severity; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_updates_severity ON public.legal_updates USING btree (severity);


--
-- Name: idx_legal_updates_type; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_legal_updates_type ON public.legal_updates USING btree (update_type);


--
-- Name: idx_oauth_providers_provider; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_oauth_providers_provider ON public.oauth_providers USING btree (provider, provider_user_id);


--
-- Name: idx_oauth_providers_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_oauth_providers_user ON public.oauth_providers USING btree (user_id);


--
-- Name: idx_oauth_states_token; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_oauth_states_token ON public.oauth_states USING btree (state_token);


--
-- Name: idx_revision_site; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_revision_site ON public.cookie_banner_revisions USING btree (site_id, revision DESC);


--
-- Name: idx_risk_matrix_severity; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_risk_matrix_severity ON public.compliance_risk_matrix USING btree (severity);


--
-- Name: idx_scan_history_scan_date; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_scan_history_scan_date ON public.scan_history USING btree (scan_date);


--
-- Name: idx_scan_history_scan_id; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_scan_history_scan_id ON public.scan_history USING btree (scan_id);


--
-- Name: idx_score_history_scan_date; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_score_history_scan_date ON public.score_history USING btree (scan_date DESC);


--
-- Name: idx_score_history_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_score_history_user ON public.score_history USING btree (user_id);


--
-- Name: idx_score_history_website; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_score_history_website ON public.score_history USING btree (website_id);


--
-- Name: idx_service_active; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_service_active ON public.cookie_services USING btree (is_active);


--
-- Name: idx_service_category; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_service_category ON public.cookie_services USING btree (category);


--
-- Name: idx_service_key; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_service_key ON public.cookie_services USING btree (service_key);


--
-- Name: idx_sessions_token; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_sessions_token ON public.user_sessions USING btree (refresh_token);


--
-- Name: idx_sessions_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_sessions_user ON public.user_sessions USING btree (user_id);


--
-- Name: idx_stats_date; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_stats_date ON public.cookie_compliance_stats USING btree (date DESC);


--
-- Name: idx_subscriptions_stripe; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_subscriptions_stripe ON public.subscriptions USING btree (stripe_subscription_id);


--
-- Name: idx_subscriptions_stripe_customer; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_subscriptions_stripe_customer ON public.subscriptions USING btree (stripe_customer_id);


--
-- Name: idx_subscriptions_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_subscriptions_user ON public.subscriptions USING btree (user_id);


--
-- Name: idx_tracked_websites_url; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_tracked_websites_url ON public.tracked_websites USING btree (url);


--
-- Name: idx_usage_user_month; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_usage_user_month ON public.deep_scan_usage USING btree (user_id, current_month);


--
-- Name: idx_user_limits_fixes; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_limits_fixes ON public.user_limits USING btree (fixes_used, fixes_limit);


--
-- Name: idx_user_limits_plan; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_limits_plan ON public.user_limits USING btree (plan_type);


--
-- Name: idx_user_modules_module; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_modules_module ON public.user_modules USING btree (module_id);


--
-- Name: idx_user_modules_status; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_modules_status ON public.user_modules USING btree (user_id, status) WHERE ((status)::text = 'active'::text);


--
-- Name: idx_user_modules_user; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_modules_user ON public.user_modules USING btree (user_id);


--
-- Name: idx_user_sessions_expires_at; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_sessions_expires_at ON public.user_sessions USING btree (expires_at);


--
-- Name: idx_user_sessions_token; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_sessions_token ON public.user_sessions USING btree (refresh_token);


--
-- Name: idx_user_sessions_user_id; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_user_sessions_user_id ON public.user_sessions USING btree (user_id);


--
-- Name: idx_users_active; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_users_active ON public.users USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_waitlist_leads_confirm_token; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_waitlist_leads_confirm_token ON public.waitlist_leads USING btree (confirm_token) WHERE (confirm_token IS NOT NULL);


--
-- Name: idx_waitlist_leads_confirmed; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_waitlist_leads_confirmed ON public.waitlist_leads USING btree (confirmed_at) WHERE (confirmed_at IS NOT NULL);


--
-- Name: idx_waitlist_leads_created_at; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_waitlist_leads_created_at ON public.waitlist_leads USING btree (created_at DESC);


--
-- Name: idx_waitlist_leads_email; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX idx_waitlist_leads_email ON public.waitlist_leads USING btree (email);


--
-- Name: legal_updates_archive_action_required_idx; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX legal_updates_archive_action_required_idx ON public.legal_updates_archive USING btree (action_required);


--
-- Name: legal_updates_archive_published_at_idx; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX legal_updates_archive_published_at_idx ON public.legal_updates_archive USING btree (published_at DESC);


--
-- Name: legal_updates_archive_severity_idx; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX legal_updates_archive_severity_idx ON public.legal_updates_archive USING btree (severity);


--
-- Name: legal_updates_archive_update_type_idx; Type: INDEX; Schema: public; Owner: complyo_user
--

CREATE INDEX legal_updates_archive_update_type_idx ON public.legal_updates_archive USING btree (update_type);


--
-- Name: v_classification_performance _RETURN; Type: RULE; Schema: public; Owner: complyo_user
--

CREATE OR REPLACE VIEW public.v_classification_performance AS
 SELECT ac.id,
    ac.update_id,
    ac.action_required,
    ac.confidence,
    ac.severity,
    ac.impact_score,
    ac.primary_action_type,
    count(f.id) AS total_feedback,
    sum(
        CASE
            WHEN ((f.feedback_type)::text = ANY ((ARRAY['explicit_helpful'::character varying, 'action_completed'::character varying])::text[])) THEN 1
            ELSE 0
        END) AS positive_feedback,
    sum(
        CASE
            WHEN ((f.feedback_type)::text = ANY ((ARRAY['explicit_not_helpful'::character varying, 'explicit_wrong'::character varying])::text[])) THEN 1
            ELSE 0
        END) AS negative_feedback,
    sum(
        CASE
            WHEN (f.user_action IS NOT NULL) THEN 1
            ELSE 0
        END) AS engaged_users,
    avg(f.time_to_action) AS avg_time_to_action,
        CASE
            WHEN (count(f.id) = 0) THEN (0)::double precision
            ELSE (((sum(
            CASE
                WHEN ((f.feedback_type)::text = ANY ((ARRAY['explicit_helpful'::character varying, 'action_completed'::character varying])::text[])) THEN 1
                ELSE 0
            END))::double precision - (sum(
            CASE
                WHEN ((f.feedback_type)::text = ANY ((ARRAY['explicit_not_helpful'::character varying, 'explicit_wrong'::character varying])::text[])) THEN 1
                ELSE 0
            END))::double precision) / (count(f.id))::double precision)
        END AS performance_score,
    ac.classified_at
   FROM (public.ai_classifications ac
     LEFT JOIN public.ai_classification_feedback f ON ((ac.id = f.classification_id)))
  GROUP BY ac.id
  ORDER BY ac.classified_at DESC;


--
-- Name: legal_updates legal_updates_auto_classify; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER legal_updates_auto_classify BEFORE INSERT ON public.legal_updates FOR EACH ROW EXECUTE FUNCTION public.trigger_auto_classification();


--
-- Name: ai_solution_cache trg_update_keywords; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trg_update_keywords BEFORE INSERT OR UPDATE ON public.ai_solution_cache FOR EACH ROW EXECUTE FUNCTION public.update_solution_keywords();


--
-- Name: cookie_banner_configs trigger_banner_revision; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trigger_banner_revision BEFORE UPDATE ON public.cookie_banner_configs FOR EACH ROW EXECUTE FUNCTION public.increment_banner_revision();


--
-- Name: oauth_states trigger_cleanup_oauth_states; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trigger_cleanup_oauth_states BEFORE INSERT ON public.oauth_states FOR EACH STATEMENT EXECUTE FUNCTION public.cleanup_expired_oauth_states();


--
-- Name: compliance_risk_matrix trigger_risk_matrix_updated_at; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trigger_risk_matrix_updated_at BEFORE UPDATE ON public.compliance_risk_matrix FOR EACH ROW EXECUTE FUNCTION public.update_risk_matrix_timestamp();


--
-- Name: subscriptions trigger_set_refund_deadline; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trigger_set_refund_deadline BEFORE INSERT ON public.subscriptions FOR EACH ROW EXECUTE FUNCTION public.set_refund_deadline();


--
-- Name: subscriptions trigger_subscriptions_timestamp; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trigger_subscriptions_timestamp BEFORE UPDATE ON public.subscriptions FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: scan_history trigger_update_website_after_scan; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trigger_update_website_after_scan AFTER INSERT ON public.scan_history FOR EACH ROW EXECUTE FUNCTION public.update_tracked_website_after_scan();


--
-- Name: user_limits trigger_user_limits_timestamp; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER trigger_user_limits_timestamp BEFORE UPDATE ON public.user_limits FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: legal_news update_legal_news_updated_at; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER update_legal_news_updated_at BEFORE UPDATE ON public.legal_news FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: rss_feed_sources update_rss_feed_sources_updated_at; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER update_rss_feed_sources_updated_at BEFORE UPDATE ON public.rss_feed_sources FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: stripe_customers update_stripe_customers_updated_at; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER update_stripe_customers_updated_at BEFORE UPDATE ON public.stripe_customers FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: complyo_user
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: ai_classification_feedback ai_classification_feedback_classification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.ai_classification_feedback
    ADD CONSTRAINT ai_classification_feedback_classification_id_fkey FOREIGN KEY (classification_id) REFERENCES public.ai_classifications(id) ON DELETE CASCADE;


--
-- Name: compliance_fixes compliance_fixes_applied_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.compliance_fixes
    ADD CONSTRAINT compliance_fixes_applied_by_fkey FOREIGN KEY (applied_by) REFERENCES public.users(id);


--
-- Name: compliance_fixes compliance_fixes_legal_change_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.compliance_fixes
    ADD CONSTRAINT compliance_fixes_legal_change_id_fkey FOREIGN KEY (legal_change_id) REFERENCES public.legal_changes(id) ON DELETE CASCADE;


--
-- Name: compliance_fixes compliance_fixes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.compliance_fixes
    ADD CONSTRAINT compliance_fixes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: cookie_banner_configs cookie_banner_configs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_configs
    ADD CONSTRAINT cookie_banner_configs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: cookie_banner_revisions cookie_banner_revisions_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.cookie_banner_revisions
    ADD CONSTRAINT cookie_banner_revisions_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(id);


--
-- Name: deep_cookie_scans deep_cookie_scans_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_cookie_scans
    ADD CONSTRAINT deep_cookie_scans_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: deep_scan_history deep_scan_history_scan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_scan_history
    ADD CONSTRAINT deep_scan_history_scan_id_fkey FOREIGN KEY (scan_id) REFERENCES public.deep_cookie_scans(id) ON DELETE CASCADE;


--
-- Name: deep_scan_usage deep_scan_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.deep_scan_usage
    ADD CONSTRAINT deep_scan_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: export_history export_history_fix_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.export_history
    ADD CONSTRAINT export_history_fix_id_fkey FOREIGN KEY (fix_id) REFERENCES public.generated_fixes(id);


--
-- Name: export_history export_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.export_history
    ADD CONSTRAINT export_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_limits(user_id);


--
-- Name: generated_fixes generated_fixes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.generated_fixes
    ADD CONSTRAINT generated_fixes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_limits(user_id);


--
-- Name: legal_change_impacts legal_change_impacts_legal_change_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_impacts
    ADD CONSTRAINT legal_change_impacts_legal_change_id_fkey FOREIGN KEY (legal_change_id) REFERENCES public.legal_changes(id) ON DELETE CASCADE;


--
-- Name: legal_change_impacts legal_change_impacts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_impacts
    ADD CONSTRAINT legal_change_impacts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: legal_change_notifications legal_change_notifications_legal_change_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_notifications
    ADD CONSTRAINT legal_change_notifications_legal_change_id_fkey FOREIGN KEY (legal_change_id) REFERENCES public.legal_changes(id) ON DELETE CASCADE;


--
-- Name: legal_change_notifications legal_change_notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_change_notifications
    ADD CONSTRAINT legal_change_notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: legal_changes legal_changes_classification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_changes
    ADD CONSTRAINT legal_changes_classification_id_fkey FOREIGN KEY (classification_id) REFERENCES public.ai_classifications(id);


--
-- Name: legal_updates legal_updates_classification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.legal_updates
    ADD CONSTRAINT legal_updates_classification_id_fkey FOREIGN KEY (classification_id) REFERENCES public.ai_classifications(id);


--
-- Name: oauth_providers oauth_providers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.oauth_providers
    ADD CONSTRAINT oauth_providers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: stripe_customers stripe_customers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.stripe_customers
    ADD CONSTRAINT stripe_customers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_modules user_modules_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_modules
    ADD CONSTRAINT user_modules_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id) ON DELETE CASCADE;


--
-- Name: user_modules user_modules_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_modules
    ADD CONSTRAINT user_modules_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: complyo_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict CHodISGbMiefA3qZd5OuTZcHtl7ai1ZxAs57jgBGu3xLQDS1YemYGANNFe3r8mb

