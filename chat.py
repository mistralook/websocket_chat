from aiohttp import web


class WSChat:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.conns = {}

    async def main_page(self, request):
        return web.FileResponse('./index.html')

    async def ws_handler(self, request):

        ws = web.WebSocketResponse()
        ws._autoclose = False
        await ws.prepare(request)

        async for msg in ws:
            try:
                data = msg.json()
            except:
                await ws.pong(b"pong")
                continue
            if data["mtype"] == "INIT":
                self.conns[data["id"]] = ws
                json = {'mtype': 'USER_ENTER', 'id': data["id"]}
                for client in self.conns.values():
                    await client.send_json(json)
            if data["mtype"] == "TEXT":
                message = data["text"]
                if data["to"]:
                    json = {'mtype': 'DM', 'id': data["id"],
                            'text': message}
                    await self.conns[data["to"]].send_json(json)
                    continue
                json = {'mtype': 'MSG', 'id': data["id"], 'text': message}
                for client in self.conns.values():
                    if ws == client:
                        continue
                    await client.send_json(json)

        leaved_client = self.find_leaved(ws)
        del self.conns[leaved_client]
        for client in self.conns.values():
            await client.send_json(
                {'mtype': 'USER_LEAVE', 'id': leaved_client})
        await ws.close()

    def find_leaved(self, ws):
        for ids in self.conns.keys():
            if self.conns[ids] == ws:
                return ids

    def run(self):
        app = web.Application()
        app.router.add_get('/', self.main_page)
        app.router.add_get('/chat', self.ws_handler)
        web.run_app(app, host=self.host, port=self.port)


if __name__ == '__main__':
    WSChat().run()
