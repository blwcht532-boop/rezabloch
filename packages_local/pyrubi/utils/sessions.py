from os.path import exists
from json import loads, dumps

class Sessions:

    def __init__(self, client:object) -> None:
        self.client = client

    def cheackSessionExists(self):
        return exists(f"{self.client.session}.l8P")
    
    def loadSessionData(self):
        return loads(open(f"{self.client.session}.l8P", encoding="UTF-8").read())
        
    def createSession(self):
        from ..methods import Methods
        methods:object = Methods(
            sessionData={},
            platform=self.client.platform,
            apiVersion=6,
            proxy=self.client.proxy,
            timeOut=self.client.timeOut,
            showProgressBar=True
        )
        print("\n>> Hi human")
        while True:
            phoneNumber:str = input("\n» Enter the phone number: ")
            try:
                sendCodeData:dict = methods.sendCode(phoneNumber=phoneNumber)
            except:
                print("» The phone number is invalid! Please try again.")
                continue

            if sendCodeData['status'] == 'SendPassKey':
                while True:
                    passKey:str = input(f'\n» Enter the pass key <{sendCodeData["hint_pass_key"]}>: ')
                    sendCodeData:dict = methods.sendCode(phoneNumber=phoneNumber, passKey=passKey)
                    
                    if sendCodeData['status'] == 'InvalidPassKey':
                        print(f'\n» Te phass key({sendCodeData["hint_pass_key"]}) is invalid! Please try again.')
                        continue
                    break
            
            while True:
                phoneCode:str = input("\n» Enter the code: ").strip()
                signInData:dict = methods.signIn(phoneNumber=phoneNumber, phoneCodeHash=sendCodeData['phone_code_hash'], phoneCode=phoneCode)
                if signInData['status'] != 'OK':
                    print("» The code is invalid! Please try again.")
                    continue
                break
            
            from ..crypto import Cryption

            sessionData = {
                'auth': Cryption.decryptRsaOaep(signInData["private_key"], signInData['auth']),
                'private_key': signInData["private_key"],
                'user': signInData['user'],
            }

            open(f"{self.client.session}.l8P", "w", encoding="UTF-8").write(dumps(sessionData, indent=4))

            def rdnm(min:int=1,max:int=9)->int:
                import random
                return random.randint(min,max)
            
            Methods(
                sessionData=sessionData,
                platform=self.client.platform,
                apiVersion=6,
                proxy=self.client.proxy,
                timeOut=self.client.timeOut,
                showProgressBar=True
            ).registerDevice(deviceModel=f"Chrom {rdnm(2,4)}")
            print(f"\n» Sign in as \"{self.client.session}\" was successful.")

            return sessionData