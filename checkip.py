#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import warnings
import aiohttp
import os
import ssl
import time
import get_ip


class Test_Ip:
    def __init__(self, loop, ipCreator, f):
        self.q = asyncio.Queue()
        self.f = f
        self.loop = loop
        self.d = dict()
        self.ipcreator = ipCreator
        print("get ipcreator")
        self.ipcreator.find_ip()
        self.generateIp = self.ipcreator.generate
        self.max = 64
        self.now = 1
        self._running = True
        self.future = None

    async def test(self, ip):
        start_time = time.time()
        try:
            async with self.session.request("GET", "https://%s/_gh/" % ip, headers={"Host": "my-project-1-1469878073076.appspot.com"}, ) as resp:
                headers = resp.headers
                server_type = headers.get('Server', '')
                len = headers.get('Content-Length', '')
                if int(len) == 86:
                    end_time = time.time()
                    time_used = end_time - start_time
                    #print(ip,"status:", resp.status ,"time_used:", time_used)
                    self.d[ip] = time_used
                    return True
                if resp.status == 503:
                    # out of quota
                    if "gws" not in server_type and "Google Frontend" not in server_type and "GFE" not in server_type:
                        return False
                    else:
                        end_time = time.time()
                        time_used = end_time - start_time
                        #print(ip, "time_used:", time_used)
                        self.d[ip] = time_used
                        return True
                else:
                    return False
        except KeyboardInterrupt as e:
            self.loop.run_until_complete(self.stop())
        except BaseException as e:
            return False
            # print(e)

    async def worker(self):
        try:
            while self._running:
                ip = await self.generateIp()
                #print("test ip")
                if ip not in self.d:
                    self.d[ip] = 0
                success = await self.test(ip)
                if success:
                    print(ip, "Success time_used:", self.d[ip])
                    await self.q.put(ip)
                else:
                    if ip in self.d:
                        del self.d[ip]
                    #print(ip, "failed")
        finally:
            self.now -= 1
            if not self.future.done():
                self.future.set_result("need task")
            #print("Task Done :", self.now)
            #self.now += 1
            ##print("start Task Sum: ", self.now)
            # self.loop.create_task(self.worker())

    async def Server(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        print("create session")
        self.loop.create_task(self.SaveIp())
        print("creat SaveIp worker")
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl_context=context, force_close=True), conn_timeout=1, read_timeout=1) as self.session:
            create = True
            print("create session Success")
            while self._running:
                if self.now < self.max and create:
                    self.now += 1
                    print("create task at", self.now)
                    #print("start Task Sum: ", self.now)
                    self.loop.create_task(self.worker())
                    if self.now == self.max:
                        self.future = asyncio.Future()
                else:
                    await self.future

    async def stop(self):
        self._running = False
        if self.future is not None:
            self.future.set_result("need stop")
        while self.now > 0:
            await asyncio.sleep(0.2)
            if(self.now == 1):
                await self.q.put("end")
            print("stopping  wait %d worker stop" % self.now)
        self.f.close()
        print("file closed")
        print("Success stop")
        return True

    async def SaveIp(self):
        while self._running:
            ip = await self.q.get()
            # await asyncio.sleep(1)
            s = ip + "|"
            self.f.write(s)
            #print("file writed", s)
        self.now -= 1


# os.fork()
# os.fork()
# os.fork()


async def SaveIp(q, f):
    global Running
    while Running:
        ip = await q.get()
        s = ip + "|"
        f.write(s)
        print("file writed", s)


try:
    ipcreator = get_ip.IpCreator()
    f = open("ip.txt", 'w')
    loop = asyncio.get_event_loop()
    testip = Test_Ip(loop, ipcreator, f)
    loop.create_task(testip.Server())
    loop.run_forever()
except KeyboardInterrupt as e:
    loop.run_until_complete(testip.stop())

finally:
    loop.stop()
    loop.close()
