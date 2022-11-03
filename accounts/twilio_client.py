from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from greatkart import settings


class TwilioOTP:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID,settings.TWILIO_AUTH_TOKEN)
        self.verify = self.client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID)

    def send(self,phone):
        phone_number= '+91'+str(phone)
        self.verify.verifications.create(to=phone_number, channel='sms')

    def check(self, phone, code):
        try:
            phone_number= '+91'+str(phone)
            result = self.verify.verification_checks.create(to=phone_number, code=code)
        except TwilioRestException:
            print('false')
            return False
        return result.status


