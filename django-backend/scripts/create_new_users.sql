-- Utility script to create new users in the fecfile-online database.
-- Edit the sample VALUES() below to create new user accounts.

-- Update authentication_account_id_seq to ensure the index is pointing to the correct value 
SELECT setval('authentication_account_id_seq', (SELECT max(id) FROM authentication_account));

-- To associate a user to additional committee ids Taking an existing committee id from the committee_master table
-- ensure the committee table doesn't have an entry in authentication_account table 
INSERT into authentication_account(
        password,
        is_superuser,
        email,
        username,
        cmtee_id,
        created_at,
        updated_at,
        is_staff,
        is_active,
        date_joined,
        tagline,
        role,
        delete_ind,
        contact,
        status
    )
VALUES
       ('pbkdf2_sha256$36000$gZSXSbOJiHED$NKQPaMEHncW8lw0y8vvRvXD/3w4vs9xXWiTvjdFAUiM=','f','egreen.ctr@fec.gov','C00601534egreen.ctr@fec.gov','C00601534',now(),now(),'f','t',now(),'', 'C_ADMIN','N','2026941307','Registered'),
       ('pbkdf2_sha256$36000$gZSXSbOJiHED$NKQPaMEHncW8lw0y8vvRvXD/3w4vs9xXWiTvjdFAUiM=','f','egreen.ctr@fec.gov','C00601229egreen.ctr@fec.gov','C00601229',now(),now(),'f','t',now(),'', 'C_ADMIN','N','2402743764','Registered'),
       ('pbkdf2_sha256$36000$gZSXSbOJiHED$NKQPaMEHncW8lw0y8vvRvXD/3w4vs9xXWiTvjdFAUiM=','f','egreen.ctr@fec.gov','C00233361egreen.ctr@fec.gov','C00233361',now(),now(),'f','t',now(),'', 'C_ADMIN','N','2402743764','Registered'),
       ('pbkdf2_sha256$36000$gZSXSbOJiHED$NKQPaMEHncW8lw0y8vvRvXD/3w4vs9xXWiTvjdFAUiM=','f','akolan.ctr@fec.gov','C00601609akolan.ctr@fec.gov','C00601609',now(),now(),'f','t',now(),'', 'C_ADMIN','N','5121234567','Registered'),
       ('pbkdf2_sha256$36000$gZSXSbOJiHED$NKQPaMEHncW8lw0y8vvRvXD/3w4vs9xXWiTvjdFAUiM=','f','akolan.ctr@fec.gov','C00670430akolan.ctr@fec.gov','C00670430',now(),now(),'f','t',now(),'', 'C_ADMIN','N','5121234567','Registered'),
       ('pbkdf2_sha256$36000$gZSXSbOJiHED$NKQPaMEHncW8lw0y8vvRvXD/3w4vs9xXWiTvjdFAUiM=','f','akolan.ctr@fec.gov','C00715672akolan.ctr@fec.gov','C00715672',now(),now(),'f','t',now(),'', 'C_ADMIN','N','5121234567','Registered');

-- Applies to bot PAC and PTY
-- Update forms_committee table with the user information 
INSERT INTO public.forms_committee(
    committeeid,
    committeename,
    street1,
    street2,
    city,
    state,
    zipcode,
    treasurerlastname,
    treasurerfirstname,
    treasurermiddlename,
    treasurerprefix,
    treasurersuffix,
    created_at,
    updated_at,
    isdeleted,
    email_on_file)
    SELECT
        cm.cmte_id,
        cm.cmte_name,
        cm.street_1,
        cm.street_2,
        cm.city,
        cm.state,
        20148,
        cm.treasurer_last_name,
        cm.treasurer_first_name,
        cm.treasurer_middle_name,
        cm.treasurer_prefix,
        cm.treasurer_suffix,
        now(),
        now(),
        false,
        aa.email
    FROM committee_master cm
    INNER JOIN  authentication_account aa ON cm.cmte_id = aa.cmtee_id
WHERE cm.cmte_id in (
  'C00601534',
  'C00601229',
  'C00233361',
  'C00601609',
  'C00670430',
  'C00715672'
 );

-- Ensure there aren't any due reports associated with the committee ids. 
Delete from cmte_current_due_reports
where cmte_id in (
  'C00601534',
  'C00601229',
  'C00233361',
  'C00601609',
  'C00670430',
  'C00715672'

);

-- Applies to PAC only using C00000422 as a template
INSERT INTO public.cmte_current_due_reports(
            cmte_id, form_type, report_type, due_date, last_update_date)
select 'C00601534', form_type, report_type, due_date, last_update_date
from public.cmte_current_due_reports
where cmte_id ='C00000422';
INSERT INTO public.cmte_current_due_reports(
            cmte_id, form_type, report_type, due_date, last_update_date)
select 'C00601609', form_type, report_type, due_date, last_update_date
from public.cmte_current_due_reports
where cmte_id ='C00000422';
INSERT INTO public.cmte_current_due_reports(
            cmte_id, form_type, report_type, due_date, last_update_date)
select 'C00601229', form_type, report_type, due_date, last_update_date
from public.cmte_current_due_reports
where cmte_id ='C00000422';
INSERT INTO public.cmte_current_due_reports(
            cmte_id, form_type, report_type, due_date, last_update_date)
select 'C00670430', form_type, report_type, due_date, last_update_date
from public.cmte_current_due_reports
where cmte_id ='C00000422';

-- Applies to PTY only using C00010603 as a template 
INSERT INTO public.cmte_current_due_reports(
            cmte_id, form_type, report_type, due_date, last_update_date)
select 'C00233361', form_type, report_type, due_date, last_update_date
from public.cmte_current_due_reports
where cmte_id ='C00010603';

INSERT INTO public.cmte_current_due_reports(
            cmte_id, form_type, report_type, due_date, last_update_date)
select 'C00715672', form_type, report_type, due_date, last_update_date
from public.cmte_current_due_reports
where cmte_id ='C00010603';


-- Applies to PAC
update committee_master set cmte_type='Q' where cmte_id in (
 'C00601534',
 'C00601609',
 'C00601229',
 'C00670430'
 );

-- Applies to PTY
update committee_master set cmte_type='X' where cmte_id in (
  'C00233361',
  'C00715672'
 );

-- Applies to both PAC and PTY
update committee_master set cmte_dsgn='B', cmte_filing_freq='M'  where cmte_id in (
  'C00601534',
  'C00601229',
  'C00233361',
  'C00601609',
  'C00670430',
  'C00715672'

);
-- PAC with 3L
UPDATE public.committee_master set cmte_type='X', cmte_dsgn='U', cmte_filing_freq='M', cmte_filed_type='4' WHERE cmte_type_category='PAC'  AND cmte_id in (
  'C00601534',
  'C00601229'
);

-- PAC without 3L
UPDATE public.committee_master set cmte_filing_freq='Q' WHERE cmte_type_category='PAC' AND cmte_id in (
  'C00601609',
  'C00670430'
);
