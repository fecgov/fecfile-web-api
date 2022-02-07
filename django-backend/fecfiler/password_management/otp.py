import datetime

from binascii import unhexlify
from datetime import datetime
from datetime import timedelta

import pytz
from django.contrib.auth.hashers import get_hasher, make_password
from django.db import connection
from django_otp.oath import TOTP
from django_otp.util import random_hex
from unittest import mock
import time

from fecfiler.settings import (
    OTP_DIGIT,
    OTP_TIME_EXPIRY,
    logger,
    OTP_MAX_RETRY,
    OTP_TIMEOUT_TIME,
    OTP_DISABLE,
    OTP_DEFAULT_PASSCODE,
)


def save_key_datbase(username, key_val, counter, unix_time):
    try:
        print(key_val)
        print(key_val.decode("utf-8"))
        decode_key = key_val.decode("utf-8")
        with connection.cursor() as cursor:
            _sql = """UPDATE public.authentication_account SET secret_key = %s, code_generated_counter = %s, updated_at = %s, code_time = %s WHERE username = %s AND delete_ind !='Y'"""
            _v = (decode_key, counter, datetime.now(), unix_time, username)
            cursor.execute(_sql, _v)
            if cursor.rowcount != 1:
                logger.debug("key save failed for username {}", username)
        return cursor.rowcount
    except Exception as e:
        logger.debug("exception occurred key save for username {}", username)


def get_current_counter_val(username):
    default_sequence = 0
    try:
        with connection.cursor() as cursor:
            _sql = """select code_generated_counter from public.authentication_account where username = %s AND delete_ind !='Y'"""
            cursor.execute(_sql, [username])
            code_counter = cursor.fetchone()[0]
            if code_counter is None:
                default_sequence
            else:
                default_sequence = int(code_counter) + 1

        return default_sequence
    except Exception as e:
        raise e


def get_last_updated_time(username):
    try:
        with connection.cursor() as cursor:
            _sql = """select updated_at from public.authentication_account where username = %s AND delete_ind !='Y'"""
            cursor.execute(_sql, [username])
            update_time = cursor.fetchone()[0]

        return update_time
    except Exception as e:
        raise e


class TOTPVerification:
    def __init__(self, username):

        self.key = make_password(username).encode("utf-8").hex()
        self.number_of_digits = OTP_DIGIT
        self.token_validity_period = OTP_TIME_EXPIRY

    @property
    def bin_key(self):
        return unhexlify(self.key.encode())

    def totp_obj(self, username):
        # create a TOTP object
        key_val = self.bin_key
        counter = get_current_counter_val(username)
        last_updated_time = get_last_updated_time(username)
        unix_time = int(time.time())
        totp = TOTP(
            key=self.bin_key,
            step=self.token_validity_period,
            t0=unix_time,
            digits=self.number_of_digits,
        )

        totp.time = time.time()
        est = pytz.timezone("US/Eastern")
        current_time_est = datetime.now(est)

        current_time_est1 = current_time_est.replace(tzinfo=None)
        upper_limit = last_updated_time + timedelta(minutes=OTP_TIMEOUT_TIME)
        upper_limit1 = upper_limit.replace(tzinfo=None)
        if counter <= OTP_MAX_RETRY:
            save_key_datbase(username, key_val, counter, unix_time)
        elif counter > OTP_MAX_RETRY and upper_limit1 < current_time_est1:
            counter = 0
            save_key_datbase(username, key_val, counter, unix_time)
        elif counter > OTP_MAX_RETRY:
            return None

        return totp

    def generate_token(self, username):

        print("value of OTP flag - register token", OTP_DISABLE)
        if OTP_DISABLE:
            token = OTP_DEFAULT_PASSCODE
        else:
            totp = self.totp_obj(username)
            if totp is None:
                return -1
            token = str(totp.token()).zfill(6)

        print(token)
        return token

    def verify_token(self, key, unix_time):
        try:
            print("value of OTP flag - verify token", OTP_DISABLE)
            if OTP_DISABLE:
                token = OTP_DEFAULT_PASSCODE
            else:
                print(key)
                print(key.encode("utf-8"))
                encode_key = key.encode("utf-8")
                totp = TOTP(
                    key=encode_key,
                    step=self.token_validity_period,
                    t0=int(unix_time),
                    digits=self.number_of_digits,
                )
                token = str(totp.token()).zfill(6)

            print(token)
            return token
        except ValueError:
            # return False, if token could not be converted to an integer
            return 0
