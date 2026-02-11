This is your product’s spine. It prevents nonsense combinations.

3.1 Severity levels

Critical: block completion. Must be fixed or explicitly overridden with justification.

High: allow completion, but force a warning and add to risks.

Medium: warn and lower confidence.

Low: informational.

3.2 Conflict matrix (starter set for V1)
Rule ID	If	And	Then	Severity	Fix Required
V-ICP-01	ICP is empty	run attempts to finalize	block run	Critical	Yes
V-PROD-01	Value prop missing	any pillar finalization	block run	Critical	Yes
V-PRICE-01	pricing.metric empty	any pricing tier exists	block run	Critical	Yes
V-CHAN-01	more than 2 primary channels	category is b2b_saas or b2b_services	flag “focus failure”	High	Yes, must pick 1 primary
V-SALES-01	sales_motion is plg	ICP is enterprise or budget_owner is “procurement”	mismatch warning	High	Requires justification or change
V-SALES-02	sales_motion is outbound_led	ICP company size is “1-10” and price is low	warn about unit economics	Medium	No
V-PRICE-02	price-to-test is very high	no proof of willingness-to-pay	missing proof	High	Yes, add validation experiment
V-TECH-01	compliance_level is high	no security or data plan nodes	block completion	Critical	Yes
V-EVID-01	competitor list empty	category not novel	missing proof	High	Yes, rerun evidence or confirm “greenfield”
V-EVID-02	pricing anchors empty	pricing decided	missing proof	High	Yes
V-EXEC-01	chosen_track is unset	user tries to export “final”	block export as final	High	Yes
V-OPS-01	execution pillar empty	user marks scenario complete	block completion	High	Yes
V-PEOPLE-01	people_and_cash pillar empty	pricing decided	warn about runway	Medium	No
V-CONT-01	override used	no justification text	block override	High	Yes
3.3 Validator outputs (machine-readable)

Validator should output state.risks.contradictions[] with:

rule_id

severity

message

paths (JSON pointers to conflicting fields)

recommended_fix (optional)

Example:

{
  "rule_id": "V-SALES-01",
  "severity": "high",
  "message": "PLG-only motion conflicts with enterprise ICP and procurement buyer. Expect long cycles and low self-serve conversion.",
  "paths": ["/decisions/sales_motion/motion", "/decisions/icp/profile/company_size", "/decisions/icp/profile/budget_owner"]
}
