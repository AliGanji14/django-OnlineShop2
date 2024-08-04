from kavenegar import *


def send_otp_code(phone_number, code):
    try:
        api = KavenegarAPI('626E6E5753583979704764556A747170537632322F6A78576E4D443653697247795A4436776773622B6D553D', )
        params = {
            'sender': '',  # optional
            'receptor': phone_number,  # multiple mobile number, split by comma
            'message': f'{code} کد تایید شما ',
        }
        response = api.sms_send(params)
        print(response)
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)
