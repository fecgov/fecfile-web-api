--DROP VIEW  public.all_receipts_transactions_view;

CREATE OR REPLACE VIEW public.all_receipts_transactions_view AS 
 SELECT sa.cmte_id,
    sa.report_id,
    rp.report_type,
    rrt.rpt_type_desc as report_desc,
    sa.line_number,
    'sched_a'::text AS transaction_table,
    sa.transaction_type,
    rt.tran_desc AS transaction_type_desc,
    sa.transaction_type_identifier,
    sa.transaction_id,
    sa.back_ref_transaction_id,
    sa.back_ref_sched_name,
    sa.entity_id,
        CASE
            WHEN e.entity_type::text = ANY (ARRAY['IND'::character varying::text, 'CAN'::character varying::text]) THEN ((((initcap(e.last_name::text) || COALESCE(', '::text || initcap(e.first_name::text), ''::text)) || COALESCE(', '::text || initcap(e.middle_name::text), ''::text)) || COALESCE(', '::text || initcap(e.preffix::text), ''::text)) || COALESCE(', '::text || initcap(e.suffix::text), ''::text))::character varying
            ELSE e.entity_name
        END AS name,
    e.street_1,
    e.street_2,
    e.city,
    e.state,
    e.zip_code,
    e.occupation,
    e.employer,
    sa.contribution_date AS transaction_date,
    sa.contribution_amount AS transaction_amount,
    sa.aggregate_amt,
    sa.purpose_description,
    sa.memo_code,
    sa.memo_text,
    sa.election_code,
    sa.election_other_description,
    sa.delete_ind,
    sa.create_date,
    sa.last_update_date,
    sa.itemized_ind AS itemized,
    '/sa/schedA'::text AS api_call,
    rt.category_type,
       CASE
            WHEN e.delete_ind = 'Y'::bpchar THEN sa.last_update_date
            ELSE NULL::timestamp without time zone
        END AS deleteddate
   FROM sched_a sa
     JOIN entity e ON e.entity_id::text = sa.entity_id::text
     JOIN ref_transaction_types rt ON rt.tran_identifier::text = sa.transaction_type_identifier::text
     JOIN reports rp ON rp.cmte_id::text = sa.cmte_id::text AND rp.report_id = sa.report_id
     JOIN ref_rpt_types rrt ON rp.report_type::text = rrt.rpt_type::text;


--DROP VIEW  public.all_disbursements_transactions_view;

CREATE OR REPLACE VIEW public.all_disbursements_transactions_view AS 
 SELECT sb.cmte_id,
    sb.report_id,
    rp.report_type,
    rrt.rpt_type_desc as report_desc,
    sb.line_number,
    'sched_b'::text AS transaction_table,
    sb.transaction_type,
    rt.tran_desc AS transaction_type_desc,
    sb.transaction_type_identifier,
    sb.transaction_id,
    sb.back_ref_transaction_id,
    sb.back_ref_sched_name,
    sb.entity_id,
        CASE
            WHEN e.entity_type::text = ANY (ARRAY['IND'::character varying::text, 'CAN'::character varying::text]) THEN ((((initcap(e.last_name::text) || COALESCE(', '::text || initcap(e.first_name::text), ''::text)) || COALESCE(', '::text || initcap(e.middle_name::text), ''::text)) || COALESCE(', '::text || initcap(e.preffix::text), ''::text)) || COALESCE(', '::text || initcap(e.suffix::text), ''::text))::character varying
            ELSE e.entity_name
        END AS name,
    e.street_1,
    e.street_2,
    e.city,
    e.state,
    e.zip_code,
    e.occupation,
    e.employer,
    sb.expenditure_date AS transaction_date,
    sb.expenditure_amount AS transaction_amount,
    sb.aggregate_amt,
    sb.expenditure_purpose AS purpose_description,
    sb.memo_code,
    sb.memo_text,
    sb.election_code,
    sb.election_other_description,
    sb.delete_ind,
    sb.create_date,
    sb.last_update_date,
    sb.itemized_ind AS itemized,
    '/sb/schedB'::text AS api_call,
    rt.category_type, 
    sb.election_year,
    sb.beneficiary_cmte_id,
       CASE
            WHEN e.delete_ind = 'Y'::bpchar THEN sb.last_update_date
            ELSE NULL::timestamp without time zone
        END AS deleteddate
   FROM sched_b sb
     JOIN entity e ON e.entity_id::text = sb.entity_id::text
     JOIN ref_transaction_types rt ON rt.tran_identifier::text = sb.transaction_type_identifier::text
     JOIN reports rp ON rp.cmte_id::text = sb.cmte_id::text AND rp.report_id = sb.report_id
     JOIN ref_rpt_types rrt ON rp.report_type::text = rrt.rpt_type::text;



--DROP VIEW  public.all_loans_transactions_view;

CREATE OR REPLACE VIEW public.all_loans_transactions_view AS 
 SELECT sc.cmte_id,
    sc.report_id,
    rp.report_type,
    rrt.rpt_type_desc as report_desc,
    sc.line_number,
    'sched_c'::text AS transaction_table,
    sc.transaction_type,
    rt.tran_desc AS transaction_type_desc,
    sc.transaction_type_identifier,
    sc.transaction_id,
    sc.entity_id,
        CASE
            WHEN e.entity_type::text = ANY (ARRAY['IND'::character varying::text, 'CAN'::character varying::text]) THEN ((((initcap(e.last_name::text) || COALESCE(', '::text || initcap(e.first_name::text), ''::text)) || COALESCE(', '::text || initcap(e.middle_name::text), ''::text)) || COALESCE(', '::text || initcap(e.preffix::text), ''::text)) || COALESCE(', '::text || initcap(e.suffix::text), ''::text))::character varying
            ELSE e.entity_name
        END AS name,
    e.street_1,
    e.street_2,
    e.city,
    e.state,
    e.zip_code,
    e.occupation,
    e.employer,
    sc.loan_amount_original,
    sc.loan_payment_to_date,
    sc.loan_balance,
    sc.loan_incurred_date,
    sc.loan_due_date,
    sc.memo_code,
    sc.memo_text,
    sc.delete_ind,
    sc.create_date,
    sc.last_update_date,
    '/sc/schedC'::text AS api_call,
    rt.category_type,
       CASE
            WHEN e.delete_ind = 'Y'::bpchar THEN sc.last_update_date
            ELSE NULL::timestamp without time zone
        END AS deleteddate
   FROM sched_c sc
     JOIN entity e ON e.entity_id::text = sc.entity_id::text
     JOIN ref_transaction_types rt ON rt.tran_identifier::text = sc.transaction_type_identifier::text
     JOIN reports rp ON rp.cmte_id::text = sc.cmte_id::text AND rp.report_id = sc.report_id
     JOIN ref_rpt_types rrt ON rp.report_type::text = rrt.rpt_type::text;




--DROP VIEW  public.all_other_transactions_view;

CREATE OR REPLACE VIEW public.all_other_transactions_view AS 
 SELECT sd.cmte_id,
    sd.report_id,
    rp.report_type,
    rrt.rpt_type_desc as report_desc,
    sd.line_num AS line_number,
    'sched_d'::text AS transaction_table,
    sd.transaction_type,
    rt.tran_desc AS transaction_type_desc,
    sd.transaction_type_identifier,
    sd.transaction_id,
    ''::text AS back_ref_transaction_id,
    ''::text AS back_ref_sched_name,
    sd.entity_id,
        CASE
            WHEN e.entity_type::text = ANY (ARRAY['IND'::character varying::text, 'CAN'::character varying::text]) THEN ((((initcap(e.last_name::text) || COALESCE(', '::text || initcap(e.first_name::text), ''::text)) || COALESCE(', '::text || initcap(e.middle_name::text), ''::text)) || COALESCE(', '::text || initcap(e.preffix::text), ''::text)) || COALESCE(', '::text || initcap(e.suffix::text), ''::text))::character varying
            ELSE e.entity_name
        END AS name,
    e.street_1,
    e.street_2,
    e.city,
    e.state,
    e.zip_code,
    e.occupation,
    e.employer,
    sd.purpose,
    sd.beginning_balance,
    sd.payment_amount,
    sd.balance_at_close,
    NULL::date AS transaction_date,
    sd.incurred_amount AS transaction_amount,
    NULL::numeric AS aggregate_amt,
    sd.purpose AS purpose_description,
    ''::text AS memo_code,
    ''::text AS memo_text,
    ''::text AS election_code,
    ''::text AS election_other_description,
    sd.delete_ind,
    sd.create_date,
    sd.last_update_date,
    NULL::text AS itemized,
    '/sd/schedD'::text AS api_call,
    rt.category_type,
       CASE
            WHEN e.delete_ind = 'Y'::bpchar THEN sd.last_update_date
            ELSE NULL::timestamp without time zone
        END AS deleteddate
   FROM sched_d sd
     JOIN entity e ON e.entity_id::text = sd.entity_id::text
     JOIN ref_transaction_types rt ON rt.tran_identifier::text = sd.transaction_type_identifier::text
     JOIN reports rp ON rp.cmte_id::text = sd.cmte_id::text AND rp.report_id = sd.report_id
     JOIN ref_rpt_types rrt ON rp.report_type::text = rrt.rpt_type::text;



