
from random import choices, randint
from time import time
from re import finditer, sub
from base64 import b64encode
from io import BytesIO
from tempfile import NamedTemporaryFile
from mutagen import mp3, File
from filetype import guess
from os import system, chmod, remove

class Tools:

    def randomTmpSession() -> str:
        return "".join(choices("abcdefghijklmnopqrstuvwxyz", k=32))
    
    def randomDeviceHash() -> str:
        return "".join(choices("0123456789", k=26))
    
    def randomRnd() -> str:
        return str(randint(-99999999, 99999999))
    
    def privateParse(private:str) -> str:
        if not private.startswith("-----BEGIN RSA PRIVATE KEY-----\n"):
            private = "-----BEGIN RSA PRIVATE KEY-----\n" + private
        
        if not private.endswith("\n-----END RSA PRIVATE KEY-----"):
            private += "\n-----END RSA PRIVATE KEY-----"

        return private

    def getState() -> int:
        return int(time()) - 150
    
    def phoneNumberParse(phoneNumber:str) -> str:
        if str(phoneNumber).startswith("0"):
            phoneNumber = phoneNumber[1:]

        elif str(phoneNumber).startswith("98"):
            phoneNumber = phoneNumber[2:]

        elif str(phoneNumber).startswith("+98"):
            phoneNumber = phoneNumber[3:]

        return phoneNumber
    
    def getChatTypeByGuid(objectGuid:str) -> str:
        for chatType in [("u0", "User"), ("g0", "Group"), ("c0", "Channel"), ("s0", "Service"), ("b0", "Bot")]:
            if objectGuid.startswith(chatType[0]): return chatType[1]
        return ""
    
    def getChatTypeByLink(link:str) -> str:
        if "rubika.ir/joing" in link: return "Group"
        elif "rubika.ir/joinc" in link: return "Channel"
    
    def checkMetadata(text):
        if text is None:
            return [], ""

        real_text = sub(r'``|\*\*|__|~~|--|@@|##|', '', text)
        metadata = []
        conflict = 0
        mentionObjectIndex = 0
        result = []

        patterns = {
            "Mono": r'\`\`([^``]*)\`\`',
            "Bold": r'\*\*([^**]*)\*\*',
            "Italic": r'\_\_([^__]*)\_\_',
            "Strike": r'\~\~([^~~]*)\~\~',
            "Underline": r'\-\-([^__]*)\-\-',
            "Mention": r'\@\@([^@@]*)\@\@',
            "Spoiler": r'\#\#([^##]*)\#\#',
        }

        for style, pattern in patterns.items():
            for match in finditer(pattern, text):
                metadata.append((match.start(), len(match.group(1)), style))

        metadata.sort()

        for start, length, style in metadata:
            if not style == "Mention":
                result.append({
                    'type': style,
                    'from_index': start - conflict,
                    'length': length,
                })
                conflict += 4
            else:
                mentionObjects = [i.group(1) for i in finditer(r'\@\(([^(]*)\)', text)]
                mentionType = Tools.getChatTypeByGuid(objectGuid=mentionObjects[mentionObjectIndex].strip()) or 'Link'

                if mentionType == 'Link':
                    result.append(
                        {
                            'from_index': start - conflict,
                            'length': length,
                            'link': {
                                'hyperlink_data': {
                                    "url": mentionObjects[mentionObjectIndex].strip()
                                },
                                'type': 'hyperlink',
                            },
                            'type': mentionType,
                        }
                    )
                else:
                    result.append(
                        {
                            'type': 'MentionText',
                            'from_index': start - conflict,
                            'length': length,
                            'mention_text_object_guid': mentionObjects[mentionObjectIndex].strip(),
                            'mention_text_object_type': mentionType
                        }
                    )
                real_text = real_text.replace(f'({mentionObjects[mentionObjectIndex]})', '')
                conflict += 6 + len(mentionObjects[mentionObjectIndex])
                mentionObjectIndex += 1
                
        return result, real_text
    
    def checkLink(url:str) -> dict:
        for i in ["http:/", "https://"]:
            if url.startswith(i): return True

    def getMimeFromByte(bytes:bytes) -> str:
        return (guess(bytes).extension or "pyrubi")
    
    def generateFileName(mime:str) -> str:
        return "Pyrubi Library {}.{}".format(randint(1, 1000), mime)
    
    def getImageSize(bytes:bytes) -> str:
        try:
            from PIL import Image
        except:
            return [1000,1000]
            # system("pip install pillow")
            # from PIL import Image

        width, height = Image.open(BytesIO(bytes)).size
        return width , height
    
    def getImageThumbnail(bytes:bytes) -> str:
        try:
            from PIL import Image
        except:
            return """iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAE/0lEQVR4nH1Y7XbrIAyTgSTd9v7P2i583T+Tr3DZck5P0wBGlmzj1Mxsmhl4zTn93sygY3Fc53HMzPxbn8e1KSXMOTHG8LljjMUeAKTfQP21AZ/vHNs5kFJa5i0AUlqcio6bmU3+oKE5J+acSCm5V5uFDoZsAHibrwDiuJJAJpX9OSeKouakuGk0pkxGmeikgooM7RyMwLlP+o3aCCw+U5bVRs55kTRuWEpBznkBP8bwdZFxM7O5i4NItXsUDESgkf04NzqoBIwxMMZYQi3pj12CcIwLeU9QfDbnRM7ZN4qZHMFyLh3iN5lkuJTfpNCFnJxSQu/dwWrMaRzGskEbvffFKa7tvS/7qTNlJ6UypwAVuMbeX/ISJNlReSMZcX8zQ9JM1CsyQ9ZyziilOCPKmMZolIxzCaqU4nuo3EwghknRGFTkkRn1NIKjjdbaG0Cy3Fr7v+kPOM3q7+/vRXbaLmpMGeOGKqPG0hgD53mi946cs8eXxpSZLbIyS1Xi3rsrEmujmcFKKZMgSikYY7yxw9/HcbydMgrqOI63gCco3pMxVav3jtaaO6pMJi0DtVZnIufshhQEDQBwQHNO34T3XMf767oW9jmX+6aUPAx077IrqlqwyZKWFo7TIQAopeA4DuScUWtFrRWlFFzXhfu+UWvFdV1oraG1tsh+nqfHuYaYmcE+Pj4mvVEALLxkTiWP3UhKCbXWpXjTqTGGM3Qcx1IDW2uotbrtnLMTQTZLaw3xin1ZKcV/e/D+fCg7mai1rln4E9eajBqfmkQEpnW2kFoFxAlM/8/PT9z37V6SVTLNTCag3jvu+8ZxHDjP09fQ8fu+lwLOWNbsF8XS7uHScbA0UDJ6zDjTWNMEoWRaOrRS8KKKtMe6uRx1SjsBkxkaiEmkyVNrxXmePpcJAwCv1wtzTnx9fXlsK1hltNa6yk5ZdHPKxrqlMUR5WY5i95Jzxufnp9e04zhwXZfH8fP5dEAqqR57/DYzJAJhkNIQZaFsyhzl5rmsbRYdor3n84neO87zxBgDj8fDY46ZGpsKbdPs8XhMMqb1R0sFx7T00BnK93g80FrzgqxNLDPT4+rnLH69Xs7ycRx4Pp9LIgJAobcMaJWRQNQwF8caxtMh5+wMvV6vhVG9yByTkbLz9KFiReNOTwsaba35hpFhADjP8+0E4JzzPH1DSqpVQTsmPd+1gnhHTQCxq929KwBwZlprS4Fm/NI57SWpCBnSvjI2w1SpxNZc7zUptAXTYGaScb52Lvd9LzHH2shxVUsJ0Rh3BmM/qAFOTxWE9n9kikowZrVTpl1dp/3hrhE2s/8A41uaeqQlRo869ZzjlH3X7quUkXEFqcok3UA7aJYeysP6yPn81iKvvRxZVkY1GfVYVSVY4IGfYp1SmiqxAlBWojEtT+wN40uTxrWezcqk7kX1mMVzTjgqfU/QSzeN5UEvSh/fXxgW+nIWFYgvblo3LaU0d4tVhhiPCkhDIjoYYzhWBWVRs1oZLrpAF0WvdIzxycKq9XIXIgp491zV0jLz1rDqBGVk9+6s45qJ0anIqNZJnaPvPoqhRLoVgMq0+0No92+EyqlO71jbhVN08u0v4NiQ7sDvHImsxM0icF0bFdDxpAYiyLgxa5g6wfH4j4EytPsdTxHajtKvtSIY0qL6l+dxjYZClHdnK4aZhlOJXiqAWD5ihu0yXNdHAOrUbt8dhn9U4atgmuDMDwAAAABJRU5ErkJggg=="""
            # system("pip install pillow")
            # from PIL import Image
            
        image = Image.open(BytesIO(bytes))
        width, height = image.size
        if height > width:
            new_height = 40
            new_width  = round(new_height * width / height)
        else:
            new_width = 40
            new_height = round(new_width * height / width)
        image = image.resize((new_width, new_height), Image.LANCZOS)
        changed_image = BytesIO()
        image.save(changed_image, format='PNG')
        return b64encode(changed_image.getvalue()).decode('UTF-8')
    
    def getVideoData(bytes:bytes) -> list:
        try:
            try:
                from moviepy.editor import VideoFileClip
            except:
                return """iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAE/0lEQVR4nH1Y7XbrIAyTgSTd9v7P2i583T+Tr3DZck5P0wBGlmzj1Mxsmhl4zTn93sygY3Fc53HMzPxbn8e1KSXMOTHG8LljjMUeAKTfQP21AZ/vHNs5kFJa5i0AUlqcio6bmU3+oKE5J+acSCm5V5uFDoZsAHibrwDiuJJAJpX9OSeKouakuGk0pkxGmeikgooM7RyMwLlP+o3aCCw+U5bVRs55kTRuWEpBznkBP8bwdZFxM7O5i4NItXsUDESgkf04NzqoBIwxMMZYQi3pj12CcIwLeU9QfDbnRM7ZN4qZHMFyLh3iN5lkuJTfpNCFnJxSQu/dwWrMaRzGskEbvffFKa7tvS/7qTNlJ6UypwAVuMbeX/ISJNlReSMZcX8zQ9JM1CsyQ9ZyziilOCPKmMZolIxzCaqU4nuo3EwghknRGFTkkRn1NIKjjdbaG0Cy3Fr7v+kPOM3q7+/vRXbaLmpMGeOGKqPG0hgD53mi946cs8eXxpSZLbIyS1Xi3rsrEmujmcFKKZMgSikYY7yxw9/HcbydMgrqOI63gCco3pMxVav3jtaaO6pMJi0DtVZnIufshhQEDQBwQHNO34T3XMf767oW9jmX+6aUPAx077IrqlqwyZKWFo7TIQAopeA4DuScUWtFrRWlFFzXhfu+UWvFdV1oraG1tsh+nqfHuYaYmcE+Pj4mvVEALLxkTiWP3UhKCbXWpXjTqTGGM3Qcx1IDW2uotbrtnLMTQTZLaw3xin1ZKcV/e/D+fCg7mai1rln4E9eajBqfmkQEpnW2kFoFxAlM/8/PT9z37V6SVTLNTCag3jvu+8ZxHDjP09fQ8fu+lwLOWNbsF8XS7uHScbA0UDJ6zDjTWNMEoWRaOrRS8KKKtMe6uRx1SjsBkxkaiEmkyVNrxXmePpcJAwCv1wtzTnx9fXlsK1hltNa6yk5ZdHPKxrqlMUR5WY5i95Jzxufnp9e04zhwXZfH8fP5dEAqqR57/DYzJAJhkNIQZaFsyhzl5rmsbRYdor3n84neO87zxBgDj8fDY46ZGpsKbdPs8XhMMqb1R0sFx7T00BnK93g80FrzgqxNLDPT4+rnLH69Xs7ycRx4Pp9LIgJAobcMaJWRQNQwF8caxtMh5+wMvV6vhVG9yByTkbLz9KFiReNOTwsaba35hpFhADjP8+0E4JzzPH1DSqpVQTsmPd+1gnhHTQCxq929KwBwZlprS4Fm/NI57SWpCBnSvjI2w1SpxNZc7zUptAXTYGaScb52Lvd9LzHH2shxVUsJ0Rh3BmM/qAFOTxWE9n9kikowZrVTpl1dp/3hrhE2s/8A41uaeqQlRo869ZzjlH3X7quUkXEFqcok3UA7aJYeysP6yPn81iKvvRxZVkY1GfVYVSVY4IGfYp1SmiqxAlBWojEtT+wN40uTxrWezcqk7kX1mMVzTjgqfU/QSzeN5UEvSh/fXxgW+nIWFYgvblo3LaU0d4tVhhiPCkhDIjoYYzhWBWVRs1oZLrpAF0WvdIzxycKq9XIXIgp491zV0jLz1rDqBGVk9+6s45qJ0anIqNZJnaPvPoqhRLoVgMq0+0No92+EyqlO71jbhVN08u0v4NiQ7sDvHImsxM0icF0bFdDxpAYiyLgxa5g6wfH4j4EytPsdTxHajtKvtSIY0qL6l+dxjYZClHdnK4aZhlOJXiqAWD5ihu0yXNdHAOrUbt8dhn9U4atgmuDMDwAAAABJRU5ErkJggg==""", [1000, 1000], 1
                # system("pip install moviepy")
                # from moviepy.editor import VideoFileClip

            with NamedTemporaryFile(delete=False, dir='.') as temp_video:
                temp_video.write(bytes)
                temp_path = temp_video.name

            chmod(temp_path, 0o777)

            try:
                from PIL import Image
            except:
                return """iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAE/0lEQVR4nH1Y7XbrIAyTgSTd9v7P2i583T+Tr3DZck5P0wBGlmzj1Mxsmhl4zTn93sygY3Fc53HMzPxbn8e1KSXMOTHG8LljjMUeAKTfQP21AZ/vHNs5kFJa5i0AUlqcio6bmU3+oKE5J+acSCm5V5uFDoZsAHibrwDiuJJAJpX9OSeKouakuGk0pkxGmeikgooM7RyMwLlP+o3aCCw+U5bVRs55kTRuWEpBznkBP8bwdZFxM7O5i4NItXsUDESgkf04NzqoBIwxMMZYQi3pj12CcIwLeU9QfDbnRM7ZN4qZHMFyLh3iN5lkuJTfpNCFnJxSQu/dwWrMaRzGskEbvffFKa7tvS/7qTNlJ6UypwAVuMbeX/ISJNlReSMZcX8zQ9JM1CsyQ9ZyziilOCPKmMZolIxzCaqU4nuo3EwghknRGFTkkRn1NIKjjdbaG0Cy3Fr7v+kPOM3q7+/vRXbaLmpMGeOGKqPG0hgD53mi946cs8eXxpSZLbIyS1Xi3rsrEmujmcFKKZMgSikYY7yxw9/HcbydMgrqOI63gCco3pMxVav3jtaaO6pMJi0DtVZnIufshhQEDQBwQHNO34T3XMf767oW9jmX+6aUPAx077IrqlqwyZKWFo7TIQAopeA4DuScUWtFrRWlFFzXhfu+UWvFdV1oraG1tsh+nqfHuYaYmcE+Pj4mvVEALLxkTiWP3UhKCbXWpXjTqTGGM3Qcx1IDW2uotbrtnLMTQTZLaw3xin1ZKcV/e/D+fCg7mai1rln4E9eajBqfmkQEpnW2kFoFxAlM/8/PT9z37V6SVTLNTCag3jvu+8ZxHDjP09fQ8fu+lwLOWNbsF8XS7uHScbA0UDJ6zDjTWNMEoWRaOrRS8KKKtMe6uRx1SjsBkxkaiEmkyVNrxXmePpcJAwCv1wtzTnx9fXlsK1hltNa6yk5ZdHPKxrqlMUR5WY5i95Jzxufnp9e04zhwXZfH8fP5dEAqqR57/DYzJAJhkNIQZaFsyhzl5rmsbRYdor3n84neO87zxBgDj8fDY46ZGpsKbdPs8XhMMqb1R0sFx7T00BnK93g80FrzgqxNLDPT4+rnLH69Xs7ycRx4Pp9LIgJAobcMaJWRQNQwF8caxtMh5+wMvV6vhVG9yByTkbLz9KFiReNOTwsaba35hpFhADjP8+0E4JzzPH1DSqpVQTsmPd+1gnhHTQCxq929KwBwZlprS4Fm/NI57SWpCBnSvjI2w1SpxNZc7zUptAXTYGaScb52Lvd9LzHH2shxVUsJ0Rh3BmM/qAFOTxWE9n9kikowZrVTpl1dp/3hrhE2s/8A41uaeqQlRo869ZzjlH3X7quUkXEFqcok3UA7aJYeysP6yPn81iKvvRxZVkY1GfVYVSVY4IGfYp1SmiqxAlBWojEtT+wN40uTxrWezcqk7kX1mMVzTjgqfU/QSzeN5UEvSh/fXxgW+nIWFYgvblo3LaU0d4tVhhiPCkhDIjoYYzhWBWVRs1oZLrpAF0WvdIzxycKq9XIXIgp491zV0jLz1rDqBGVk9+6s45qJ0anIqNZJnaPvPoqhRLoVgMq0+0No92+EyqlO71jbhVN08u0v4NiQ7sDvHImsxM0icF0bFdDxpAYiyLgxa5g6wfH4j4EytPsdTxHajtKvtSIY0qL6l+dxjYZClHdnK4aZhlOJXiqAWD5ihu0yXNdHAOrUbt8dhn9U4atgmuDMDwAAAABJRU5ErkJggg==""", [1000, 1000], 1
                # system("pip install pillow")
                # from PIL import Image

            with VideoFileClip(temp_path) as clip:
                duration = clip.duration
                resolution = clip.size
                thumbnail = clip.get_frame(0)
                thumbnail_image = Image.fromarray(thumbnail)
                thumbnail_buffer = BytesIO()
                thumbnail_image.save(thumbnail_buffer, format="JPEG")
                thumbnail_b64 = b64encode(thumbnail_buffer.getvalue()).decode("UTF-8")
                clip.close()

            remove(temp_path)

            return thumbnail_b64, resolution, duration
        except:
            return """iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAE/0lEQVR4nH1Y7XbrIAyTgSTd9v7P2i583T+Tr3DZck5P0wBGlmzj1Mxsmhl4zTn93sygY3Fc53HMzPxbn8e1KSXMOTHG8LljjMUeAKTfQP21AZ/vHNs5kFJa5i0AUlqcio6bmU3+oKE5J+acSCm5V5uFDoZsAHibrwDiuJJAJpX9OSeKouakuGk0pkxGmeikgooM7RyMwLlP+o3aCCw+U5bVRs55kTRuWEpBznkBP8bwdZFxM7O5i4NItXsUDESgkf04NzqoBIwxMMZYQi3pj12CcIwLeU9QfDbnRM7ZN4qZHMFyLh3iN5lkuJTfpNCFnJxSQu/dwWrMaRzGskEbvffFKa7tvS/7qTNlJ6UypwAVuMbeX/ISJNlReSMZcX8zQ9JM1CsyQ9ZyziilOCPKmMZolIxzCaqU4nuo3EwghknRGFTkkRn1NIKjjdbaG0Cy3Fr7v+kPOM3q7+/vRXbaLmpMGeOGKqPG0hgD53mi946cs8eXxpSZLbIyS1Xi3rsrEmujmcFKKZMgSikYY7yxw9/HcbydMgrqOI63gCco3pMxVav3jtaaO6pMJi0DtVZnIufshhQEDQBwQHNO34T3XMf767oW9jmX+6aUPAx077IrqlqwyZKWFo7TIQAopeA4DuScUWtFrRWlFFzXhfu+UWvFdV1oraG1tsh+nqfHuYaYmcE+Pj4mvVEALLxkTiWP3UhKCbXWpXjTqTGGM3Qcx1IDW2uotbrtnLMTQTZLaw3xin1ZKcV/e/D+fCg7mai1rln4E9eajBqfmkQEpnW2kFoFxAlM/8/PT9z37V6SVTLNTCag3jvu+8ZxHDjP09fQ8fu+lwLOWNbsF8XS7uHScbA0UDJ6zDjTWNMEoWRaOrRS8KKKtMe6uRx1SjsBkxkaiEmkyVNrxXmePpcJAwCv1wtzTnx9fXlsK1hltNa6yk5ZdHPKxrqlMUR5WY5i95Jzxufnp9e04zhwXZfH8fP5dEAqqR57/DYzJAJhkNIQZaFsyhzl5rmsbRYdor3n84neO87zxBgDj8fDY46ZGpsKbdPs8XhMMqb1R0sFx7T00BnK93g80FrzgqxNLDPT4+rnLH69Xs7ycRx4Pp9LIgJAobcMaJWRQNQwF8caxtMh5+wMvV6vhVG9yByTkbLz9KFiReNOTwsaba35hpFhADjP8+0E4JzzPH1DSqpVQTsmPd+1gnhHTQCxq929KwBwZlprS4Fm/NI57SWpCBnSvjI2w1SpxNZc7zUptAXTYGaScb52Lvd9LzHH2shxVUsJ0Rh3BmM/qAFOTxWE9n9kikowZrVTpl1dp/3hrhE2s/8A41uaeqQlRo869ZzjlH3X7quUkXEFqcok3UA7aJYeysP6yPn81iKvvRxZVkY1GfVYVSVY4IGfYp1SmiqxAlBWojEtT+wN40uTxrWezcqk7kX1mMVzTjgqfU/QSzeN5UEvSh/fXxgW+nIWFYgvblo3LaU0d4tVhhiPCkhDIjoYYzhWBWVRs1oZLrpAF0WvdIzxycKq9XIXIgp491zV0jLz1rDqBGVk9+6s45qJ0anIqNZJnaPvPoqhRLoVgMq0+0No92+EyqlO71jbhVN08u0v4NiQ7sDvHImsxM0icF0bFdDxpAYiyLgxa5g6wfH4j4EytPsdTxHajtKvtSIY0qL6l+dxjYZClHdnK4aZhlOJXiqAWD5ihu0yXNdHAOrUbt8dhn9U4atgmuDMDwAAAABJRU5ErkJggg==""", [1000, 1000], 1
        
    def getVoiceDuration(bytes:bytes) -> int:
        file = BytesIO()
        file.write(bytes)
        file.seek(0)
        return mp3.MP3(file).info.length
    
    def getMusicArtist(bytes:bytes) -> str:
        try:
            audio = File(BytesIO(bytes), easy=True)

            if audio and 'artist' in audio:
                return audio['artist'][0]
            
            return "L8PBOT"
        except Exception:
            return "L8PBOT"