import datetime 
import time

host_path="C:/Windows/System32/drivers/etc/hosts"
redirect="127.0.0.1"

end_time=datetime.datetime(2024,11,3)
sites_list=["www.facebook.com","www.instagram.com"]

while True:
    if datetime.datetime.now()<end_time:
        print("start blocking")
        with open(host_path,"r+") as host_file:
            content=host_file.read()
            for website in sites_list:
                if website not in content:
                    host_file.write(redirect+" "+website+"\n")
                else:
                    pass
    else:
        with open(host_path,"r+") as host_file:
            content=host_file.readlines()
            host_file.seek(0)
            for lines in content:
                if not any(website in lines for website in sites_list):
                    host_file.write(lines)
        host_file.truncate()
    time.sleep(5)
            


