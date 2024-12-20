import asyncio
import aiohttp
import time
from colorama import Fore, init
from fake_useragent import UserAgent
import os

# 初始化colorama以支持Windows系统上的颜色输出
init()

# 初始化UserAgent对象用于随机生成User-Agent
ua = UserAgent()

# 请求头模板
headers_template = {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
}

async def read_proxies(filename='proxy.txt'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f'{Fore.RED}加载代理时发生错误: {e}{Fore.RESET}')
        return []

async def read_or_generate_ua():
    ua_file = 'useragent.txt'
    if os.path.exists(ua_file):
        with open(ua_file, 'r', encoding='utf-8') as file:
            return file.read().strip()
    else:
        new_ua = ua.random
        with open(ua_file, 'w', encoding='utf-8') as file:
            file.write(new_ua)
        return new_ua

async def load_sessions(filename='accounts.txt'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return [line.strip().split(':') for line in file if line.strip() and ':' in line]
    except Exception as e:
        print(f'{Fore.RED}加载账户时发生错误: {e}{Fore.RESET}')
        return []

async def coday(url, method='GET', payload_data=None, headers=None, proxy=None):
    if headers is None:
        headers = headers_template.copy()
    
    if 'User-Agent' not in headers:
        ua_string = await read_or_generate_ua()
        headers['User-Agent'] = ua_string
    
    try:
        connector = aiohttp.TCPConnector()
        
        if proxy:
            # 解析代理类型并设置连接器
            proxy_type = proxy.split('://')[0]
            if proxy_type == 'socks5':
                connector = aiohttp.SocksConnector.from_url(proxy)
            elif proxy_type in ['http', 'https']:
                connector = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            if method == 'GET':
                async with session.get(url, proxy=proxy) as response:
                    response.raise_for_status()
                    return await response.json()
            else:  # POST
                async with session.post(url, proxy=proxy, json=payload_data) as response:
                    response.raise_for_status()
                    return await response.json()
    except aiohttp.ClientResponseError as e:
        print(f'{Fore.RED}错误: {e}{Fore.RESET}')

async def login_and_check_in(email, password, proxy):
    print(f'\n尝试登录邮箱: {email}')
    sign_in_payload = {'email': email, 'password': password}
    sign_in = await coday("https://apix.securitylabs.xyz/v1/auth/signin-user", 'POST', sign_in_payload, proxy=proxy)
    
    if sign_in and 'accessToken' in sign_in:
        headers = headers_template.copy()
        headers['Authorization'] = f"Bearer {sign_in['accessToken']}"
        print(f'{Fore.GREEN}登录成功！正在获取用户详情...{Fore.RESET}')

        user = await coday("https://apix.securitylabs.xyz/v1/users", headers=headers, proxy=proxy)
        user_id = user.get('id')
        dip_token_balance = user.get('dipTokenBalance')
        if user_id:
            print(f"用户ID: {user_id} | 当前积分: {dip_token_balance}")

            print("尝试每日签到...")
            checkin = await coday(f"https://apix.securitylabs.xyz/v1/users/earn/{user_id}", headers=headers, proxy=proxy)
            if checkin and 'tokensToAward' in checkin:
                print(f'{Fore.GREEN}签到成功！获得积分: {checkin["tokensToAward"]}{Fore.RESET}')
            else:
                print(f'{Fore.YELLOW}暂时无法签到。{Fore.RESET}')
    else:
        print(f'{Fore.RED}登录失败，邮箱: {email}{Fore.RESET}')

async def main():
    sessions = await load_sessions()
    proxies = await read_proxies()
    if not sessions or not proxies:
        print("未找到账户或代理。")
        return

    # 确保代理数量足够
    while len(proxies) < len(sessions):
        proxies.append(None)  # 没有足够的代理时使用None

    while True:
        print("\n开始所有账户的每日签到过程...")

        for i, (email, password) in enumerate(sessions):
            await login_and_check_in(email, password, proxies[i])

        print("所有账户处理完毕。等待24小时以进行下次签到...")
        await asyncio.sleep(24 * 60 * 60)  # 等待24小时

if __name__ == "__main__":
    asyncio.run(main())
