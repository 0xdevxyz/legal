# Backend-Fix: Doppelter Query-String in success_url

## Problem
`stripe_routes.py:225` hängte `?session_id={CHECKOUT_SESSION_ID}` an die `success_url` an.
Das Frontend liefert aber bereits `?success=true&session_id={CHECKOUT_SESSION_ID}`.

**Resultat:** `...?success=true&session_id=xyz?session_id=xyz`

Das zweite `?` startet einen neuen (ungültigen) Query-String. Stripe übergibt den session_id
korrekt als `cs_test_...`, aber der URL-Parser gibt einen korrupten Wert weiter → `verify-checkout` schlägt mit 400 fehl.

## Fix (stripe_routes.py)

```diff
- success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
+ success_url=request.success_url,
```

Zusätzlich: Logging-Zeile vor dem `stripe.checkout.Session.create()`-Call:
```python
logger.info(f"Checkout success_url={request.success_url}")
```

## DEV-Mode-Pfad (unverändert, korrekt)
`stripe_routes.py:188`:
```python
success_url = request.success_url.replace("{CHECKOUT_SESSION_ID}", mock_session_id)
```
→ Funktioniert korrekt, da `.replace()` den Platzhalter in der bereits vollständigen URL substituiert.
