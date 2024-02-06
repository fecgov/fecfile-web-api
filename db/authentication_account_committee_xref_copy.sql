-- Add temp extension 
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add temp cmtee_id column in user_user 
ALTER TABLE
    user_user
ADD
    cmtee_id VARCHAR(9);

-- Add user_user records from authentication_account
INSERT INTO
    user_user
SELECT
    gen_random_uuid(),
    coalesce(
        password,
        encode(gen_random_bytes(32), 'hex' :: text)
    ) AS password,
    last_login,
    is_superuser,
    username,
    first_name,
    last_name,
    email,
    is_staff,
    is_active,
    date_joined,
    null,
    cmtee_id
FROM
    authentication_account;

-- Add cross ref committee_membership records for users
INSERT INTO
    committee_accounts_membership
SELECT
    nextval('committee_accounts_membership_id_seq'),
    'COMMITTEE_ADMINISTRATOR',
    ca.id,
    u.id
FROM
    user_user u
    INNER JOIN committee_accounts ca ON u.cmtee_id = ca.committee_id;

-- Drop temp cmtee_id column in user_user 
ALTER TABLE
    user_user DROP COLUMN cmtee_id;

-- Drop temp extension
DROP EXTENSION pgcrypto;