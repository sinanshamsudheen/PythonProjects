import phonenumbers
from phonenumbers import timezone,geocoder,carrier

number=input("enter the number with +__ :")
phone=phonenumbers.parse(number)
car=carrier.name_for_number(phone)
zone=timezone.time_zones_for_number(phone)
loc=geocoder.description_for_number(phone)

print(f"{phone}\ncarrier: {car}\nTime zone: {zone}\nDescription: {loc}")