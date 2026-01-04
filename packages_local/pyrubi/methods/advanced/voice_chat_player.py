import asyncio
import rubpy
import pathlib
import time
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer

async def heartbeat(client: "rubpy.Client", chat_guid: str, voice_chat_id: str):
    while True:
        try:
            await client.get_group_voice_chat_updates(chat_guid, voice_chat_id, int(time.time()))
            await asyncio.sleep(10)

        except (rubpy.exceptions.InvalidAuth, rubpy.exceptions.InvalidInput):
            break

        except Exception:
            continue

class AudioFileTrack(MediaStreamTrack):
    kind: str = 'audio'

    def __init__(self, player):
        super().__init__() 
        self.player = player

    async def recv(self):
        return await self.player.audio.recv()

async def speaking(
        client: "rubpy.Client",
        chat_guid: str,
        voice_chat_id: str
) -> None:
    while True:
        input = {
            'chat_guid': chat_guid,
            'voice_chat_id': voice_chat_id,
            'activity': 'Speaking',
            'participant_object_guid': client.guid,
        }
        try:
            await client.builder('sendGroupVoiceChatActivity', input=input)
            await asyncio.sleep(1)
        
        except (rubpy.exceptions.InvalidAuth, rubpy.exceptions.InvalidInput):
            break

        except Exception:
            continue

class VoiceChatPlayer:
    async def voice_chat_player(
            self: "rubpy.Client",
            chat_guid: str,
            media: "pathlib.Path",
            loop: bool = False,
    ):
        voice_chat = (await self.create_group_voice_chat(chat_guid) if chat_guid.startswith('g0') else
                      await self.create_channel_voice_chat(chat_guid))
        voice_chat_id = voice_chat.find_keys('voice_chat_id')
        self.logger.info(f'Voice chat created and started on chat guid: {chat_guid} and voice id: {voice_chat_id}...')

        pc = RTCPeerConnection()
        # Make a Player for file
        track = AudioFileTrack(MediaPlayer(media, media.split('.')[-1], loop=loop, decode=True))
        # Add file for connection
        pc.addTrack(track)
        # Make a sdp
        sdp_offer_local = await pc.createOffer()
        await pc.setLocalDescription(sdp_offer_local)

        input = dict(
            chat_guid=chat_guid,
            voice_chat_id=voice_chat_id,
            sdp_offer_data=sdp_offer_local.sdp,
            self_object_guid=self.guid,
        )
        connect = await self.builder('joinGroupVoiceChat', input=input)
        sdp_offer = connect.sdp_answer_data

        input = dict(
            chat_guid=chat_guid,
            voice_chat_id=voice_chat_id,
            action='Unmute',
            participant_object_guid=self.guid,
        )
        await self.builder('setGroupVoiceChatState', input=input)
        asyncio.create_task(speaking(self, chat_guid, voice_chat_id))
        remote_description = RTCSessionDescription(sdp_offer, 'answer')
        asyncio.create_task(heartbeat(self, chat_guid, voice_chat_id))
        await pc.setRemoteDescription(remote_description)

        @pc.on('iceconnectionstatechange')
        def on_iceconnectionstatechange():
            self.logger.info(f'ICE connection state is: {pc.iceConnectionState}')

        @pc.on('connectionstatechange')
        def on_connectionstatechange():
            self.logger.info(f'Connection state is: {pc.connectionState}')

        @pc.on('track')
        def on_track(event):
            self.logger.info(f'Track {event}')




