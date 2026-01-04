from json import dumps, loads
from tqdm import tqdm
from urllib3 import PoolManager
from websocket import create_connection, _exceptions as wsExceptions
from ..utils import Configs
from time import sleep
from threading import Thread
from ..utils import Exceptions
import os

class Network:

    def __init__(self, methods:object) -> None:
        self.methods = methods
        self.sessionData = methods.sessionData
        self.crypto = methods.crypto
        self.http = PoolManager(proxy_url=methods.proxy) if methods.proxy else PoolManager()

    def getServer(self, type):
        if type == "api":
            from random import randint
            return f"https://messengerg2c{randint(2, 3)}.iranlms.ir"
        else:
            from random import choice
            return choice(list(loads(self.http.request("GET", "https://getdcmess.iranlms.ir/").data.decode())["data"]["socket"].values()))

    def request(self, method:str, input:dict={}, tmpSession:bool=False, attempt:int = 0, maxAttempt:int=2):
        url:str = self.getServer("api")
        platform:str = self.methods.platform.lower()
        apiVersion:int = self.methods.apiVersion

        if platform in ["rubx", "rubikax"]:
            client:dict = Configs.clients["android"]
            client["package"] = "ir.rubx.bapp"
        
        elif platform in ["android"]:
            client:dict = Configs.clients["android"]

        else:
            client:dict = Configs.clients["web"]

        data = {
            "api_version": str(apiVersion),
            "tmp_session" if tmpSession else
            "auth": self.crypto.auth if tmpSession else
            self.crypto.changeAuthType(self.sessionData["auth"]) if apiVersion > 5 else
            self.sessionData["auth"],
            "data_enc": self.crypto.encrypt(
                dumps({
                    "method": method,
                    "input": input,
                    "client": client
                })
            )
        }

        headers:dict = {
            "Referer": "https://web.rubika.ir/",
            "Content-Type": "application/json; charset=utf-8"
        }

        if self.sessionData and apiVersion > 5:
            data["sign"] = self.crypto.makeSignFromData(data["data_enc"])

        while True:
            result = self.http.request(
                method="POST",
                url=url,
                headers=headers,
                body = dumps(data).encode(),
                timeout=self.methods.timeOut
            )

            try:
                result = loads(self.crypto.decrypt(loads(result.data.decode("UTF-8"))["data_enc"]))
            except:
                attempt += 1

                if attempt > maxAttempt:
                    raise
                
                continue

            if result["status"] == "OK":
                if not self.sessionData:
                    result["data"]["tmp_session"] = self.crypto.auth

                return result["data"]
            
            else:
                raise {
                    "INVALID_AUTH": Exceptions.InvalidAuth(),
                    "NOT_REGISTERED": Exceptions.NotRegistered(),
                    "INVALID_INPUT": Exceptions.InvalidInput(),
                    "TOO_REQUESTS": Exceptions.TooRequests()
                }[result["status_det"]]

    def handShake(self):
        global ws

        def sendData(mode:int):
            ws.send(dumps(
                {
                    "api_version": "6",
                    "auth": self.sessionData["auth"],
                    "method": "handShake"
                } if mode == 0 else {}
            ))

        def keepAlive():
            while True:
                try:
                    self.methods.getChatsUpdates()
                    sleep(60)
                    sendData(1)
                except Exceptions.NotRegistered or Exceptions.InvalidAuth:
                    print("» Invalid session data! Please enter a valid data of your account.")
                    directory = os.getcwd()
                    for filename in os.listdir(directory):  
                        if filename.endswith('.l8P'):  
                            new_filename = filename[:-4] + '.old-l8P'  
                            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))  
                            print(f'Renamed: {filename} to {new_filename}')
                    os._exit(0)
                except Exceptions.TooRequests:
                    print("» TooRequests.")
                    break
                except:
                    continue

        print("» Connecting to the web socket...")
        wsServer:str = self.getServer("socket")
        Thread(target=keepAlive, daemon=True).start()

        while True:
            try:
                ws = create_connection(url=wsServer)
                sendData(0)

                if loads(ws.recv()).get("status") == "OK":
                    print("» Connected.")

                    while True:
                        recv:dict = loads(ws.recv())

                        if recv.get("type") == "messenger":
                            yield loads(self.crypto.decrypt(recv.get("data_enc")))

            except wsExceptions.WebSocketConnectionClosedException or wsExceptions.WebSocketAddressException:
                print("» The websocket connection was disconnected! Reconnecting...")
                continue

    def upload(self, file:str | bytes, fileName:str=None, chunkSize:int=131072):
        from ..utils import Tools

        if isinstance(file, str):
            if Tools.checkLink(url=file):
                file:bytes = self.http.request(method="GET", url=file).data
                mime:str = Tools.getMimeFromByte(bytes=file)
                fileName = fileName or Tools.generateFileName(mime=mime)
            else:
                fileName = fileName or file
                mime = file.split(".")[-1]
                file = open(file, "rb").read()

        elif not isinstance(file, bytes):
            raise FileNotFoundError("Enter a valid path or url or bytes of file.")
        else:
            mime = Tools.getMimeFromByte(bytes=file)
            fileName = fileName or Tools.generateFileName(mime=mime)

        def send_chunk(data, maxAttempts=2):
            for attempt in range(maxAttempts):
                try:
                    response = self.http.request(
                        "POST",
                        url=requestSendFileData["upload_url"],
                        headers=header,
                        body=data
                    )
                    return loads(response.data.decode("UTF-8"))
                except Exception:
                    print(f"\n» Error uploading file! (Attempt {attempt + 1}/{maxAttempts})")
            
            print("\n» Failed to upload the file!")

        requestSendFileData:dict = self.methods.requestSendFile(
            fileName = fileName,
            mime = mime,
            size = len(file)
        )

        header = {
            "auth": self.sessionData["auth"],
            "access-hash-send": requestSendFileData["access_hash_send"],
            "file-id": requestSendFileData["id"],
        }

        totalParts = (len(file) + chunkSize - 1) // chunkSize

        if self.methods.showProgressBar:
            processBar = tqdm(
                desc=f"Uploading {fileName}",
                total=len(file),
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        for partNumber in range(1, totalParts + 1):
            startIdx = (partNumber - 1) * chunkSize
            endIdx = min(startIdx + chunkSize, len(file))
            header["chunk-size"] = str(endIdx - startIdx)
            header["part-number"] = str(partNumber)
            header["total-part"] = str(totalParts)
            data = file[startIdx:endIdx]
            hashFileReceive = send_chunk(data)
            
            if self.methods.showProgressBar:
                processBar.update(len(data))

            if not hashFileReceive:
                return
            
            if partNumber == totalParts:

                if not hashFileReceive["data"]:
                    return
                
                requestSendFileData["file"] = file
                requestSendFileData["access_hash_rec"] = hashFileReceive["data"]["access_hash_rec"]
                requestSendFileData["file_name"] = fileName
                requestSendFileData["mime"] = mime
                requestSendFileData["size"] = len(file)
                return requestSendFileData
            
    def download(self, accessHashRec:str, fileId:str, dcId:str, size:int, fileName:str, chunkSize:int=262143, attempt:int=0, maxAttempts:int=2):
        headers:dict = {
            "auth": self.sessionData["auth"],
            "access-hash-rec": accessHashRec,
            "dc-id": dcId,
            "file-id": fileId,
            "Host": f"messenger{dcId}.iranlms.ir",
            "client-app-name": "Main",
            "client-app-version": "3.5.7",
            "client-package": "app.rbmain.a",
            "client-platform": "Android",
            "Connection": "Keep-Alive",
            "Content-Type": "application/json",
            "User-Agent": "okhttp/3.12.1"
        }


        response = self.http.request(
            "POST",
            url=f"https://messenger{dcId}.iranlms.ir/GetFile.ashx",
            headers=headers,
            preload_content=False
        )

        data:bytes = b""

        if self.methods.showProgressBar:
            processBar = tqdm(
                desc=f"Downloading {fileName}",
                total=size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        for downloadedData in response.stream(chunkSize):
            try:
                if downloadedData:
                    data += downloadedData
                    if self.methods.showProgressBar:
                        processBar.update(len(downloadedData))

                if len(data) >= size:
                    return data
            except Exception:
                if attempt <= maxAttempts:
                    attempt += 1
                    print(f"\n» Error downloading file! (Attempt {attempt}/{maxAttempts})")
                    continue

                raise TimeoutError("Failed to download the file!")