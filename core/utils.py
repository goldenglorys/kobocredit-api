import json
import requests
import cloudinary


def generate_qrcode(instance):
    # necessary details needed to be put in qrcode
    details = {
        'first_name': instance.first_name,
        'last_name': instance.last_name,
        'ref_num': instance.ref_num,
        'email': instance.email,
        'id': instance.id
    }
    stringified_details = json.dumps(details) # convert details to JSON
    data = { 'data': stringified_details, 'size': '150x150' }
    # generate qrcode base on stringified_details from api
    res = requests.get('https://api.qrserver.com/v1/create-qr-code/', params=data)
    # upload qrcode to cloudinary
    qrcode_info = cloudinary.uploader.upload(res.content)
    return qrcode_info
