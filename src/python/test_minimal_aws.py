from request_server.request_server import send_request_py
import time

## Recibe run_id
run_id = int(send_request_py("10.0.1.11:8888", 2, [])[0])-1

with open(f"archivo_{run_id}.json", "w") as file:
   file.write("HOLA!!")
   time.sleep(3)